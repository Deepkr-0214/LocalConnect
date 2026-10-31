from django.urls import path, include

urlpatterns = [
    path('', include('landing.urls')),
    path('', include('customer.urls')),
    path('', include('vendor.urls')),
]
