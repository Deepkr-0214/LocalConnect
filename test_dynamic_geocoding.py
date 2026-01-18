"""
Comprehensive Test Suite for Dynamic Vendor Location Geocoding System
Tests the complete flow: address input -> geocoding -> coordinates saved -> map display
"""

import os
import sys
import sqlite3
import requests
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geocode import GeocodeService
from models.models import db, Vendor, Customer, Order, MenuItem
from app import app


class GeocodingTestSuite:
    """Test suite for dynamic geocoding vendor location system"""
    
    def __init__(self):
        self.geocode_service = GeocodeService()
        self.test_results = []
        self.db_path = os.path.join(os.getcwd(), "instance", "database.db")
        
    def log_result(self, test_name, status, message=""):
        """Log test result"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {
            'timestamp': timestamp,
            'test': test_name,
            'status': status,
            'message': message
        }
        self.test_results.append(result)
        
        # Print to console
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} [{test_name}] {message}")
    
    def test_geocoding_service(self):
        """Test 1: Verify geocoding service can convert addresses to coordinates"""
        print("\n" + "="*70)
        print("TEST 1: Geocoding Service Functionality")
        print("="*70)
        
        test_addresses = {
            'Delhi': 'Delhi, India',
            'Mumbai': 'Mumbai, India',
            'Bangalore': 'Bangalore, India',
            'Kolkata': 'Kolkata, India'
        }
        
        for city, address in test_addresses.items():
            lat, lon = self.geocode_service.get_coordinates(address)
            
            if lat is not None and lon is not None:
                self.log_result(
                    f"Geocoding_{city}",
                    "PASS",
                    f"{address} -> ({lat}, {lon})"
                )
            else:
                self.log_result(
                    f"Geocoding_{city}",
                    "FAIL",
                    f"Could not geocode {address}"
                )
    
    def test_vendor_coordinates_saved(self):
        """Test 2: Verify coordinates are saved when vendors register"""
        print("\n" + "="*70)
        print("TEST 2: Vendor Coordinates Saved on Registration")
        print("="*70)
        
        with app.app_context():
            # Query all vendors with addresses
            vendors = Vendor.query.filter(Vendor.business_address != None).limit(5).all()
            
            if not vendors:
                self.log_result(
                    "Vendor_Query",
                    "FAIL",
                    "No vendors with addresses found"
                )
                return
            
            for vendor in vendors:
                if vendor.latitude and vendor.longitude:
                    self.log_result(
                        f"Vendor_{vendor.id}_Coordinates",
                        "PASS",
                        f"{vendor.business_name}: ({vendor.latitude}, {vendor.longitude})"
                    )
                else:
                    self.log_result(
                        f"Vendor_{vendor.id}_Coordinates",
                        "FAIL",
                        f"{vendor.business_name}: Missing coordinates"
                    )
    
    def test_api_endpoint(self):
        """Test 3: Verify API endpoint returns correct vendor location data"""
        print("\n" + "="*70)
        print("TEST 3: API Endpoint /api/vendor/<id>/location")
        print("="*70)
        
        with app.app_context():
            vendors = Vendor.query.filter(
                Vendor.latitude != None,
                Vendor.longitude != None
            ).limit(3).all()
            
            if not vendors:
                self.log_result(
                    "API_Data_Found",
                    "FAIL",
                    "No vendors with coordinates found"
                )
                return
            
            with app.test_client() as client:
                for vendor in vendors:
                    # Test API response
                    response = client.get(f'/api/vendor/{vendor.id}/location')
                    
                    if response.status_code == 200:
                        data = response.get_json()
                        
                        checks = {
                            'id': data.get('id') == vendor.id,
                            'latitude': data.get('latitude') is not None,
                            'longitude': data.get('longitude') is not None,
                            'name': data.get('name') == vendor.business_name
                        }
                        
                        if all(checks.values()):
                            self.log_result(
                                f"API_Vendor_{vendor.id}",
                                "PASS",
                                f"All fields returned correctly"
                            )
                        else:
                            failed = [k for k, v in checks.items() if not v]
                            self.log_result(
                                f"API_Vendor_{vendor.id}",
                                "FAIL",
                                f"Missing fields: {', '.join(failed)}"
                            )
                    else:
                        self.log_result(
                            f"API_Vendor_{vendor.id}",
                            "FAIL",
                            f"HTTP {response.status_code}"
                        )
    
    def test_map_route(self):
        """Test 4: Verify map route is accessible"""
        print("\n" + "="*70)
        print("TEST 4: Map Display Route")
        print("="*70)
        
        with app.app_context():
            vendors = Vendor.query.filter(
                Vendor.latitude != None,
                Vendor.longitude != None
            ).limit(2).all()
            
            if not vendors:
                self.log_result(
                    "Map_Route_Data",
                    "FAIL",
                    "No vendors with coordinates found"
                )
                return
            
            with app.test_client() as client:
                for vendor in vendors:
                    # Route should be /map/<vendor_id>
                    response = client.get(f'/map/{vendor.id}')
                    
                    if response.status_code == 200:
                        self.log_result(
                            f"Map_Route_{vendor.id}",
                            "PASS",
                            f"Map template renders successfully"
                        )
                    else:
                        self.log_result(
                            f"Map_Route_{vendor.id}",
                            "FAIL",
                            f"HTTP {response.status_code}"
                        )
    
    def test_geocoding_completeness(self):
        """Test 5: Verify all vendors with addresses have coordinates"""
        print("\n" + "="*70)
        print("TEST 5: Geocoding Completeness Check")
        print("="*70)
        
        with app.app_context():
            # Get all vendors
            all_vendors = Vendor.query.count()
            vendors_with_address = Vendor.query.filter(
                Vendor.business_address != None
            ).count()
            vendors_geocoded = Vendor.query.filter(
                Vendor.latitude != None,
                Vendor.longitude != None
            ).count()
            
            self.log_result(
                "Vendor_Statistics",
                "PASS",
                f"Total: {all_vendors} | With Address: {vendors_with_address} | Geocoded: {vendors_geocoded}"
            )
            
            # Check for vendors with addresses but no coordinates
            ungeocoded = Vendor.query.filter(
                Vendor.business_address != None,
                (Vendor.latitude == None) | (Vendor.longitude == None)
            ).all()
            
            if ungeocoded:
                vendor_names = [v.business_name for v in ungeocoded]
                self.log_result(
                    "Ungeocoded_Vendors",
                    "WARNING",
                    f"{len(ungeocoded)} vendors need geocoding: {', '.join(vendor_names)}"
                )
            else:
                self.log_result(
                    "Ungeocoded_Vendors",
                    "PASS",
                    "All vendors with addresses are geocoded"
                )
    
    def test_location_validation(self):
        """Test 6: Verify coordinates are valid (within India bounds)"""
        print("\n" + "="*70)
        print("TEST 6: Location Validation (India Bounds)")
        print("="*70)
        
        # India bounds approximately
        INDIA_LAT_MIN, INDIA_LAT_MAX = 8.0, 35.5
        INDIA_LON_MIN, INDIA_LON_MAX = 68.0, 97.0
        
        with app.app_context():
            vendors = Vendor.query.filter(
                Vendor.latitude != None,
                Vendor.longitude != None
            ).all()
            
            for vendor in vendors:
                lat_valid = INDIA_LAT_MIN <= vendor.latitude <= INDIA_LAT_MAX
                lon_valid = INDIA_LON_MIN <= vendor.longitude <= INDIA_LON_MAX
                
                if lat_valid and lon_valid:
                    self.log_result(
                        f"Location_Validation_{vendor.id}",
                        "PASS",
                        f"{vendor.business_name}: ({vendor.latitude}, {vendor.longitude})"
                    )
                else:
                    self.log_result(
                        f"Location_Validation_{vendor.id}",
                        "WARNING",
                        f"{vendor.business_name}: Out of bounds ({vendor.latitude}, {vendor.longitude})"
                    )
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*70)
        print("TEST REPORT SUMMARY")
        print("="*70)
        
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warnings = len([r for r in self.test_results if r['status'] == 'WARNING'])
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        
        if failed == 0:
            print("\n🎉 All tests passed! Dynamic geocoding system is operational.")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Please review the logs above.")
        
        # Save report to file
        report_file = "test_geocoding_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return failed == 0
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "█"*70)
        print("DYNAMIC VENDOR LOCATION GEOCODING TEST SUITE")
        print("█"*70)
        
        self.test_geocoding_service()
        self.test_vendor_coordinates_saved()
        self.test_api_endpoint()
        self.test_map_route()
        self.test_geocoding_completeness()
        self.test_location_validation()
        
        success = self.generate_report()
        
        return success


def main():
    """Main test runner"""
    print("Starting Geocoding Test Suite...")
    
    # Initialize test suite
    test_suite = GeocodingTestSuite()
    
    # Run all tests
    success = test_suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
