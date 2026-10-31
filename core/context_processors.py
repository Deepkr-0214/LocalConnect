from django.conf import settings

def common_context(request):
    """Provides common context variables for template rendering compatibility."""
    return {
        'session': request.session,
        'user_name': request.session.get('user_name', ''),
        'user_id': request.session.get('user_id'),
        'user_role': request.session.get('user_role', ''),
        'user_email': request.session.get('user_email', ''),
        'RAZORPAY_KEY_ID': getattr(settings, 'RAZORPAY_KEY_ID', ''),
    }
