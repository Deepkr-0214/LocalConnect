# LocalConnect - Session Issue Fix Guide

## Problem
Users are being redirected to the sign-up page with "Session expired. Please login again." when accessing restaurant pages.

## What I Fixed

### 1. Session Configuration
- Made sessions permanent by default (24-hour lifetime)
- Added `session.permanent = True` to all login/signup processes
- Improved session validation logic

### 2. Decorator Issues
- Simplified `@customer_required` decorator
- Removed aggressive session clearing
- Added debug logging to track session issues

### 3. Route Protection
- Fixed `@app.before_request` to not interfere with API routes
- Improved endpoint filtering for session checks

## How to Test the Fix

### Step 1: Create Test Accounts
```bash
python create_test_accounts.py
```

### Step 2: Start the Server
```bash
python app.py
```

### Step 3: Test Login Flow
1. Go to http://127.0.0.1:5000
2. Click "Sign In"
3. Use test credentials:
   - Customer: `test@customer.com` / `test123`
   - Vendor: `test@vendor.com` / `test123`

### Step 4: Test Restaurant Access
1. After logging in as customer, go to:
   - http://127.0.0.1:5000/customer/food-restaurants
   - Click on any restaurant
2. Should NOT redirect to sign-up page

## Debug Information
- Added console logging to track session data
- Check browser console and server logs for debug messages
- Session data is now persistent across page loads

## Quick Commands
```bash
# Setup and install dependencies
python setup.bat

# Create test accounts
python create_test_accounts.py

# Start server
python app.py
# OR
start_server.bat
```

## Common Issues & Solutions

### Issue: Still getting redirected
**Solution**: Clear browser cookies and try again

### Issue: Database errors
**Solution**: Delete `instance/database.db` and restart server

### Issue: Import errors
**Solution**: Run `pip install -r requirements.txt`

## Test URLs
- Home: http://127.0.0.1:5000
- Sign In: http://127.0.0.1:5000/signin
- Customer Dashboard: http://127.0.0.1:5000/customer/dashboard
- Restaurants: http://127.0.0.1:5000/customer/food-restaurants
- Example Restaurant: http://127.0.0.1:5000/customer/vendor/1