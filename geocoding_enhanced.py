"""
Enhanced Geocoding Service with Comprehensive Logging and Fallback Strategies

This module provides robust address-to-coordinates geocoding using multiple APIs:
1. Primary: OpenStreetMap Nominatim (free, no API key)
2. Fallback: Google Maps Geocoding API (if API key provided)
3. Fallback Strategy: Simplified address retry logic

Features:
- Detailed logging of all geocoding attempts
- Exponential backoff retry logic
- Rate limiting compliance (1 request/second for Nominatim)
- Comprehensive error handling and reporting
- API response validation
- User-Agent headers (required by Nominatim)
"""

import requests
import time
import re
import logging
from typing import Tuple, Optional
from datetime import datetime

# Configure logging for geocoding operations
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [GEOCODING] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

class GeocodingError(Exception):
    """Custom exception for geocoding failures"""
    pass

class GeocodeServiceEnhanced:
    """
    Production-grade geocoding service with multiple fallback strategies
    """
    
    # Nominatim API configuration
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    NOMINATIM_USER_AGENT = "LocalConnect/1.0 (vendor-location-service)"
    NOMINATIM_RATE_LIMIT = 1.0  # seconds between requests
    NOMINATIM_TIMEOUT = 10  # seconds
    
    # Google Maps API configuration (optional fallback)
    GOOGLE_MAPS_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    GOOGLE_MAPS_API_KEY = None  # Set via environment if available
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # seconds
    BACKOFF_MULTIPLIER = 2.0
    
    # Common Indian cities for fallback parsing
    INDIAN_STATES = {
        'andaman and nicobar': 'Andaman and Nicobar Islands',
        'andhra pradesh': 'Andhra Pradesh',
        'arunachal pradesh': 'Arunachal Pradesh',
        'assam': 'Assam',
        'bihar': 'Bihar',
        'chhattisgarh': 'Chhattisgarh',
        'dadra and nagar haveli': 'Dadra and Nagar Haveli',
        'daman and diu': 'Daman and Diu',
        'delhi': 'Delhi',
        'goa': 'Goa',
        'gujarat': 'Gujarat',
        'haryana': 'Haryana',
        'himachal pradesh': 'Himachal Pradesh',
        'jharkhand': 'Jharkhand',
        'karnataka': 'Karnataka',
        'kerala': 'Kerala',
        'ladakh': 'Ladakh',
        'lakshadweep': 'Lakshadweep',
        'madhya pradesh': 'Madhya Pradesh',
        'maharashtra': 'Maharashtra',
        'manipur': 'Manipur',
        'meghalaya': 'Meghalaya',
        'mizoram': 'Mizoram',
        'nagaland': 'Nagaland',
        'odisha': 'Odisha',
        'puducherry': 'Puducherry',
        'punjab': 'Punjab',
        'rajasthan': 'Rajasthan',
        'sikkim': 'Sikkim',
        'tamil nadu': 'Tamil Nadu',
        'telangana': 'Telangana',
        'tripura': 'Tripura',
        'uttar pradesh': 'Uttar Pradesh',
        'uttarakhand': 'Uttarakhand',
        'west bengal': 'West Bengal'
    }
    
    def __init__(self, google_api_key: Optional[str] = None):
        """
        Initialize the geocoding service
        
        Args:
            google_api_key: Optional Google Maps API key for fallback
        """
        self.GOOGLE_MAPS_API_KEY = google_api_key
        logger.info("GeocodeServiceEnhanced initialized")
        if google_api_key:
            logger.info("Google Maps fallback API key configured")
        logger.info(f"Using primary service: OpenStreetMap Nominatim")
        
        # Last request time for rate limiting
        self._last_nominatim_request = 0
    
    def geocode(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Main geocoding method with fallback strategies
        
        Args:
            address: The address string to geocode
            
        Returns:
            Tuple of (latitude, longitude) or (None, None) if all methods fail
            
        Process:
            1. Try full address with Nominatim
            2. Try simplified (city, state) if full fails
            3. Try Google Maps if available
            4. Return (None, None) if all fail
        """
        
        if not address or not address.strip():
            logger.error("Empty address provided to geocode()")
            return None, None
        
        logger.info(f"═" * 80)
        logger.info(f"🔍 GEOCODING REQUEST: '{address}'")
        logger.info(f"═" * 80)
        
        # Step 1: Try full address with Nominatim
        logger.info(f"Step 1: Attempting full address with Nominatim API...")
        lat, lon = self._geocode_nominatim(address)
        if lat and lon:
            logger.info(f"✅ SUCCESS with full address: ({lat:.4f}, {lon:.4f})")
            return lat, lon
        
        # Step 2: Try simplified address (city, state)
        logger.info(f"Step 2: Full address failed. Attempting simplified address...")
        simplified = self._extract_city_state(address)
        if simplified != address:
            logger.info(f"   Simplified to: '{simplified}'")
            lat, lon = self._geocode_nominatim(simplified)
            if lat and lon:
                logger.info(f"✅ SUCCESS with simplified address: ({lat:.4f}, {lon:.4f})")
                return lat, lon
        else:
            logger.warning(f"   Could not simplify address (no state detected)")
        
        # Step 3: Try just city name
        logger.info(f"Step 3: Simplified address failed. Attempting city-only search...")
        city = self._extract_city(address)
        if city and city != address:
            logger.info(f"   City extracted: '{city}'")
            lat, lon = self._geocode_nominatim(city)
            if lat and lon:
                logger.info(f"✅ SUCCESS with city-only search: ({lat:.4f}, {lon:.4f})")
                return lat, lon
        
        # Step 4: Try Google Maps if available
        if self.GOOGLE_MAPS_API_KEY:
            logger.info(f"Step 4: Nominatim exhausted. Attempting Google Maps fallback...")
            lat, lon = self._geocode_google_maps(address)
            if lat and lon:
                logger.info(f"✅ SUCCESS with Google Maps: ({lat:.4f}, {lon:.4f})")
                return lat, lon
        else:
            logger.warning(f"Step 4: Google Maps fallback not available (no API key)")
        
        # All methods failed
        logger.error(f"❌ GEOCODING FAILED for address: '{address}'")
        logger.error(f"   All geocoding strategies exhausted")
        logger.info(f"═" * 80)
        return None, None
    
    def _geocode_nominatim(self, address: str, retry_count: int = 0) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode using OpenStreetMap Nominatim API
        
        Args:
            address: Address to geocode
            retry_count: Current retry attempt number
            
        Returns:
            Tuple of (latitude, longitude) or (None, None)
        """
        
        # Respect rate limiting
        time_since_last = time.time() - self._last_nominatim_request
        if time_since_last < self.NOMINATIM_RATE_LIMIT:
            sleep_time = self.NOMINATIM_RATE_LIMIT - time_since_last
            logger.debug(f"   Rate limiting: waiting {sleep_time:.2f}s...")
            time.sleep(sleep_time)
        
        try:
            logger.debug(f"   Making Nominatim request (attempt {retry_count + 1}/{self.MAX_RETRIES + 1})")
            
            # Build request parameters
            params = {
                'q': address.strip(),
                'format': 'json',
                'limit': 1,
                'countrycodes': 'in',  # Restrict to India
                'timeout': self.NOMINATIM_TIMEOUT
            }
            
            # Build headers with User-Agent (required by Nominatim)
            headers = {
                'User-Agent': self.NOMINATIM_USER_AGENT,
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate'
            }
            
            logger.debug(f"   URL: {self.NOMINATIM_URL}")
            logger.debug(f"   Params: {params}")
            logger.debug(f"   User-Agent: {headers['User-Agent']}")
            
            # Make the API request
            response = requests.get(
                self.NOMINATIM_URL,
                params=params,
                headers=headers,
                timeout=self.NOMINATIM_TIMEOUT
            )
            
            # Record last request time
            self._last_nominatim_request = time.time()
            
            logger.debug(f"   Response Status: {response.status_code}")
            
            # Handle HTTP status codes
            if response.status_code == 200:
                logger.debug(f"   Response received successfully")
                data = response.json()
                
                if isinstance(data, list) and len(data) > 0:
                    result = data[0]
                    latitude = float(result.get('lat'))
                    longitude = float(result.get('lon'))
                    
                    logger.debug(f"   Parsed response: lat={latitude:.4f}, lon={longitude:.4f}")
                    logger.info(f"   ✓ Nominatim returned valid coordinates: ({latitude:.4f}, {longitude:.4f})")
                    
                    return latitude, longitude
                else:
                    logger.warning(f"   Empty response from Nominatim (no results for this address)")
                    logger.debug(f"   Response body: {data}")
                    return None, None
            
            elif response.status_code == 429:  # Rate limited
                logger.warning(f"   HTTP 429: Rate limited by Nominatim")
                if retry_count < self.MAX_RETRIES:
                    wait_time = self.RETRY_DELAY * (self.BACKOFF_MULTIPLIER ** retry_count)
                    logger.info(f"   Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    return self._geocode_nominatim(address, retry_count + 1)
                else:
                    logger.error(f"   Max retries exceeded after rate limit")
                    return None, None
            
            elif response.status_code == 400:
                logger.warning(f"   HTTP 400: Bad request from Nominatim")
                logger.debug(f"   Response: {response.text}")
                return None, None
            
            elif response.status_code >= 500:
                logger.warning(f"   HTTP {response.status_code}: Server error")
                if retry_count < self.MAX_RETRIES:
                    wait_time = self.RETRY_DELAY * (self.BACKOFF_MULTIPLIER ** retry_count)
                    logger.info(f"   Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    return self._geocode_nominatim(address, retry_count + 1)
                else:
                    logger.error(f"   Max retries exceeded after server error")
                    return None, None
            
            else:
                logger.error(f"   HTTP {response.status_code}: Unexpected status code")
                logger.debug(f"   Response: {response.text}")
                return None, None
        
        except requests.exceptions.Timeout:
            logger.warning(f"   ⏱️  Request timeout (>{self.NOMINATIM_TIMEOUT}s)")
            if retry_count < self.MAX_RETRIES:
                wait_time = self.RETRY_DELAY * (self.BACKOFF_MULTIPLIER ** retry_count)
                logger.info(f"   Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                return self._geocode_nominatim(address, retry_count + 1)
            else:
                logger.error(f"   Max retries exceeded after timeout")
                return None, None
        
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"   🌐 Connection error: {e}")
            if retry_count < self.MAX_RETRIES:
                wait_time = self.RETRY_DELAY * (self.BACKOFF_MULTIPLIER ** retry_count)
                logger.info(f"   Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                return self._geocode_nominatim(address, retry_count + 1)
            else:
                logger.error(f"   Max retries exceeded after connection error")
                return None, None
        
        except Exception as e:
            logger.error(f"   ❌ Unexpected error: {type(e).__name__}: {e}")
            return None, None
    
    def _geocode_google_maps(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode using Google Maps API (fallback)
        
        Args:
            address: Address to geocode
            
        Returns:
            Tuple of (latitude, longitude) or (None, None)
        """
        
        if not self.GOOGLE_MAPS_API_KEY:
            logger.debug("   Google Maps API key not configured")
            return None, None
        
        try:
            logger.debug(f"   Making Google Maps request")
            
            params = {
                'address': address,
                'components': 'country:IN',
                'key': self.GOOGLE_MAPS_API_KEY
            }
            
            response = requests.get(self.GOOGLE_MAPS_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK' and len(data.get('results', [])) > 0:
                    location = data['results'][0]['geometry']['location']
                    latitude = location['lat']
                    longitude = location['lng']
                    
                    logger.info(f"   ✓ Google Maps returned valid coordinates: ({latitude:.4f}, {longitude:.4f})")
                    return latitude, longitude
                else:
                    logger.warning(f"   Google Maps returned status: {data.get('status')}")
                    return None, None
            else:
                logger.warning(f"   Google Maps HTTP {response.status_code}")
                return None, None
        
        except Exception as e:
            logger.error(f"   Google Maps error: {e}")
            return None, None
    
    def _extract_city_state(self, address: str) -> str:
        """
        Extract city and state from address for simplified retry
        
        Args:
            address: Full address string
            
        Returns:
            Simplified "City, State" string or original address if extraction fails
        """
        
        if not address:
            return address
        
        address_lower = address.lower()
        
        # Look for state names
        for state_key, state_name in self.INDIAN_STATES.items():
            if state_key in address_lower:
                # Try to extract city name before state
                # Pattern: City Name, State
                match = re.search(
                    rf'([a-zA-Z\s]+),\s*{re.escape(state_key)}',
                    address_lower,
                    re.IGNORECASE
                )
                
                if match:
                    city = match.group(1).strip()
                    logger.debug(f"   Extracted: city='{city}', state='{state_name}'")
                    return f"{city}, {state_name}"
                else:
                    # No city found, just return state
                    logger.debug(f"   Extracted state only: '{state_name}'")
                    return state_name
        
        logger.debug(f"   Could not extract city/state from address")
        return address
    
    def _extract_city(self, address: str) -> Optional[str]:
        """
        Extract just the city name from address
        
        Args:
            address: Full address string
            
        Returns:
            City name or None if not found
        """
        
        if not address:
            return None
        
        # Try to get first part before comma or state
        parts = address.split(',')
        if parts:
            # Get the last meaningful part (usually city)
            for part in reversed(parts):
                stripped = part.strip()
                # Skip state names
                if stripped.lower() not in self.INDIAN_STATES and len(stripped) > 2:
                    logger.debug(f"   Extracted city: '{stripped}'")
                    return stripped
        
        return None


# For backward compatibility with existing code
def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Backward compatible function that uses the enhanced geocoding service
    
    Args:
        address: Address to geocode
        
    Returns:
        Tuple of (latitude, longitude) or (None, None)
    """
    service = GeocodeServiceEnhanced()
    return service.geocode(address)


if __name__ == "__main__":
    # Test the geocoding service
    print("\n" + "=" * 80)
    print("GEOCODING SERVICE TEST")
    print("=" * 80)
    
    service = GeocodeServiceEnhanced()
    
    # Test addresses
    test_addresses = [
        "Q.no-57/21 Chhota Govindpur, Jamshedpur Jharkhand-831015",
        "Bengaluru, Karnataka",
        "Vadodara, Gujarat",
        "Delhi",
        "Mumbai, Maharashtra",
    ]
    
    for address in test_addresses:
        lat, lon = service.geocode(address)
        print()
