from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from core.models import Customer, Vendor


def customer_required(f):
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        user_role = request.session.get('user_role')

        if not user_id or user_role != 'customer':
            messages.error(request, 'Please login to access this page.')
            return redirect('sign_in')

        customer = Customer.objects.filter(id=user_id).first()
        if not customer:
            request.session.flush()
            messages.error(request, 'Account not found. Please login again.')
            return redirect('sign_in')

        response = f(request, *args, **kwargs)
        if hasattr(response, '__getitem__'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
    return decorated_function


def vendor_required(f):
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        user_role = request.session.get('user_role')

        if not user_id or user_role != 'vendor':
            messages.error(request, 'Access denied. Vendor login required.')
            return redirect('sign_in')

        vendor = Vendor.objects.filter(id=user_id).first()
        if not vendor:
            request.session.flush()
            messages.error(request, 'Vendor account not found. Please login again.')
            return redirect('sign_in')

        response = f(request, *args, **kwargs)
        if hasattr(response, '__getitem__'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
    return decorated_function
