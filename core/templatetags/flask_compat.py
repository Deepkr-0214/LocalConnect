import json
from django import template
from django.urls import reverse, NoReverseMatch
from django.templatetags.static import static as django_static

register = template.Library()

@register.filter(name='to_json')
def to_json(value):
    try:
        return json.dumps(value)
    except Exception:
        return '[]'

@register.filter(name='get_item')
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return getattr(dictionary, str(key), None)

@register.filter(name='multiply')
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''
