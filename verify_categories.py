"""
Quick verification script to check if all category routes are accessible
Run this after starting the Flask server
"""

import requests
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://127.0.0.1:5000"

# Categories to test
categories = [
    ('Garage', '/customer/garage'),
    ('Electronics', '/customer/electronics'),
    ('Fashion', '/customer/fashion'),
    ('Grocery', '/customer/grocery'),
    ('Pharmacy', '/customer/pharmacy'),
    ('Food & Restaurant', '/customer/food-restaurants'),
]

print(f"\n{Fore.CYAN}{'='*60}")
print(f"{Fore.CYAN}Category Routes Verification")
print(f"{Fore.CYAN}{'='*60}\n")

# Note: These routes require authentication, so they will redirect to login
# We're just checking if the routes exist (not 404)

for name, route in categories:
    url = BASE_URL + route
    try:
        response = requests.get(url, allow_redirects=False, timeout=5)
        
        # 302 = redirect to login (expected for protected routes)
        # 200 = success (if somehow authenticated)
        # 404 = route not found (BAD)
        
        if response.status_code == 302:
            print(f"{Fore.GREEN}✓ {name:20} - Route exists (redirects to login)")
        elif response.status_code == 200:
            print(f"{Fore.GREEN}✓ {name:20} - Route accessible")
        elif response.status_code == 404:
            print(f"{Fore.RED}✗ {name:20} - Route NOT FOUND")
        else:
            print(f"{Fore.YELLOW}? {name:20} - Status: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}✗ Server not running at {BASE_URL}")
        break
    except Exception as e:
        print(f"{Fore.RED}✗ {name:20} - Error: {str(e)}")

print(f"\n{Fore.CYAN}{'='*60}")
print(f"{Fore.CYAN}Verification Complete!")
print(f"{Fore.CYAN}{'='*60}\n")

print(f"{Fore.YELLOW}Note: Routes showing 'redirects to login' is CORRECT behavior.")
print(f"{Fore.YELLOW}This means the routes exist and are protected by @customer_required.\n")
