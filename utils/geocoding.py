"""
Geocoding utilities for converting addresses to coordinates
"""
import requests
import time

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
        
        # Parameters for the request
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        
        # Headers (Nominatim requires a User-Agent)
        headers = {
            'User-Agent': 'LocalConnect/1.0 (contact@localconnect.com)'
        }
        
        # Make the request
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                latitude = float(data[0]['lat'])
                longitude = float(data[0]['lon'])
                print(f"Geocoded '{address}' to ({latitude}, {longitude})")
                
                # Respect Nominatim's rate limit (1 request per second)
                time.sleep(1)
                
                return latitude, longitude
            else:
                print(f"No results found for address: {address}")
                return None, None
        else:
            print(f"Geocoding request failed with status code: {response.status_code}")
            return None, None
            
    except requests.exceptions.Timeout:
        print(f"Geocoding request timed out for address: {address}")
        return None, None
    except Exception as e:
        print(f"Error geocoding address '{address}': {e}")
        return None, None
