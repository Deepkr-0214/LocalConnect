import json
from jinja2 import Environment, pass_context
from django.urls import reverse, NoReverseMatch
from django.templatetags.static import static
from django.middleware.csrf import get_token
from django.contrib import messages as django_messages
from django.conf import settings

# Common aliases mapping Flask endpoint names to Django URL pattern names
ENDPOINT_ALIASES = {
    'change_password': 'customer_change_password',
    'map_view': 'map_vendor',
    'admin_delete_vendors_page': 'admin_delete_vendors',
    'delete_all_vendors': 'admin_delete_all_vendors',
    'add_vendor_offer': 'vendor_offers_add',
    'edit_vendor_offer': 'vendor_offers_edit',
    'delete_vendor_offer': 'vendor_offers_delete',
    'get_vendor_offer': 'vendor_offers_get',
    'get_vendor_offers': 'vendor_offers',
    'get_vendor_offers_list': 'vendor_offers_list',
    'toggle_item_availability': 'toggle_item',
    'delete_menu_item': 'delete_menu_item',
}


def url_for(endpoint, **kwargs):
    if endpoint == 'static':
        filename = kwargs.get('filename', '')
        return static(filename)

    lookup_endpoint = ENDPOINT_ALIASES.get(endpoint, endpoint)
    try:
        return reverse(lookup_endpoint, kwargs=kwargs)
    except NoReverseMatch:
        try:
            return reverse(lookup_endpoint, args=list(kwargs.values()))
        except NoReverseMatch:
            if lookup_endpoint != endpoint:
                try:
                    return reverse(endpoint, kwargs=kwargs)
                except NoReverseMatch:
                    try:
                        return reverse(endpoint, args=list(kwargs.values()))
                    except NoReverseMatch:
                        pass
            return f"/{endpoint.strip('/')}/"


@pass_context
def get_flashed_messages(context, with_categories=False):
    request = context.get('request')
    if not request:
        return []
    storage = django_messages.get_messages(request)
    if with_categories:
        # Map Django tags ('error', 'success', 'warning', 'info') to Flask categories
        return [(msg.tags or 'info', str(msg)) for msg in storage]
    return [str(msg) for msg in storage]


def to_json_filter(value):
    try:
        return json.dumps(value)
    except Exception:
        return '[]'


def get_item_filter(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return getattr(dictionary, str(key), None)


def multiply_filter(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': reverse,
        'url_for': url_for,
        'get_flashed_messages': get_flashed_messages,
        'RAZORPAY_KEY_ID': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    })
    env.filters.update({
        'tojson': to_json_filter,
        'to_json': to_json_filter,
        'get_item': get_item_filter,
        'multiply': multiply_filter,
    })
    return env
