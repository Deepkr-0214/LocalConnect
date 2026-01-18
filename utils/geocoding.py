"""
Geocoding utilities for converting addresses to coordinates
"""
import requests
import time
import re

def extract_city_state(address):
    """
    Extract city and state from address if geocoding fails with full address.
    Helps handle addresses like "Q.no-57/21 Chhota Govindpur, Jamshedpur Jharkhand-831015"
    
    Args:
        address (str): The full address
        
    Returns:
        str: Extracted city/state or original address if not found
    """
    if not address:
        return address
    
    # Common Indian states and their variations
    states = {
        'jharkhand': 'Jharkhand',
        'bihar': 'Bihar',
        'delhi': 'Delhi',
        'haryana': 'Haryana',
        'uttar pradesh': 'Uttar Pradesh',
        'maharashtra': 'Maharashtra',
        'karnataka': 'Karnataka',
        'tamil nadu': 'Tamil Nadu',
        'west bengal': 'West Bengal',
        'punjab': 'Punjab',
        'rajasthan': 'Rajasthan',
        'telangana': 'Telangana',
        'gujarati': 'Gujarat',
    }
    
    address_lower = address.lower()
    
    # Look for state names
    for state_key, state_name in states.items():
        if state_key in address_lower:
            # Extract city name before state (if available)
            # Pattern: City Name, State
            match = re.search(rf'([a-zA-Z\s]+),\s*{state_key}', address_lower, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                return f"{city}, {state_name}"
            else:
                # Just return state if city not found
                return state_name
    
    return address

def geocode_address(address):
    """
    Convert an address string to latitude and longitude using Nominatim (OpenStreetMap).
    
    Args:
        address (str): The address to geocode
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if geocoding fails
    """
    if not address or not address.strip():
        return None, None
    
    try:
        # Nominatim API endpoint
        url = "https://nominatim.openstreetmap.org/search"
        
        # Parameters for the request (using params dict to ensure proper encoding)
        params = {
            'q': address.strip(),
            'format': 'json',
            'limit': 1,
            'country': 'India',  # Restrict search to India
            'countrycodes': 'in'  # ISO code for India
        }
        
        # Headers (Nominatim requires a User-Agent)
        headers = {
            'User-Agent': 'LocalConnect/1.0 (contact@localconnect.com)',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'application/json'
        }
        
        # Make the request with better error handling
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
        except requests.exceptions.ConnectTimeout:
            print(f"✗ Connection timeout while geocoding: {address}")
            return None, None
        except requests.exceptions.ReadTimeout:
            print(f"✗ Read timeout while geocoding: {address}")
            return None, None
        except requests.exceptions.ConnectionError as e:
            print(f"✗ Connection error while geocoding '{address}': {e}")
            return None, None
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                latitude = float(data[0]['lat'])
                longitude = float(data[0]['lon'])
                print(f"✓ Geocoded '{address}' to ({latitude:.4f}, {longitude:.4f})")
                
                # Respect Nominatim's rate limit (1 request per second)
                time.sleep(0.5)
                
                return latitude, longitude
            else:
                print(f"✗ No results found for address: {address}")
                
                # Try with simplified address (city, state)
                print(f"  → Attempting simplified address...")
                simplified = extract_city_state(address)
                if simplified != address:
                    print(f"  → Trying: {simplified}")
                    time.sleep(0.5)
                    params['q'] = simplified
                    
                    try:
                        response = requests.get(url, params=params, headers=headers, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data and len(data) > 0:
                                latitude = float(data[0]['lat'])
                                longitude = float(data[0]['lon'])
                                print(f"✓ Geocoded simplified address to ({latitude:.4f}, {longitude:.4f})")
                                time.sleep(0.5)
                                return latitude, longitude
                    except Exception as e:
                        print(f"✗ Error with simplified address: {e}")
                
                return None, None
        elif response.status_code == 400:
            print(f"✗ Bad request (400) for address: {address}")
            print(f"  Trying simplified address...")
            
            # Try with simplified address on 400 error
            simplified = extract_city_state(address)
            if simplified != address:
                print(f"  → Trying: {simplified}")
                time.sleep(0.5)
                params['q'] = simplified
                
                try:
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            latitude = float(data[0]['lat'])
                            longitude = float(data[0]['lon'])
                            print(f"✓ Geocoded simplified address to ({latitude:.4f}, {longitude:.4f})")
                            time.sleep(0.5)
                            return latitude, longitude
                except Exception as e:
                    print(f"✗ Error: {e}")
            
            return None, None
        else:
            print(f"✗ Geocoding request failed with status code: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"✗ Error geocoding address '{address}': {e}")
        return None, None
