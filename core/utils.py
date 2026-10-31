import os
import sys
import logging
import warnings
from django.conf import settings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
import razorpay

from utils.twilio_notifications import TwilioNotifications
from utils.enhanced_notifications import EnhancedNotifications
from utils.category_labels import get_category_labels
from geocoding_enhanced import GeocodeServiceEnhanced

# Razorpay client
try:
    razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
except Exception:
    razorpay_client = None

# Enhanced notifications
notifier = EnhancedNotifications()
enhanced_notifications = notifier
twilio_notifications = TwilioNotifications()

# Geocoding service (initialized silently)
old_stdout = sys.stdout
old_stderr = sys.stderr
try:
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    geocode_service = GeocodeServiceEnhanced()
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr
