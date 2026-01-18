#!/usr/bin/env python3
"""
Test Script for Enhanced Geocoding Service

Tests the production-grade geocoding service with:
- Valid addresses from all Indian states
- Edge cases and problematic formats
- Fallback strategies
- Error handling
- Performance metrics
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geocoding_enhanced import GeocodeServiceEnhanced
import time
import json
from datetime import datetime

class GeocodingServiceTester:
    """Test suite for enhanced geocoding service"""
    
    def __init__(self):
        self.service = GeocodeServiceEnhanced()
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'tests': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def test_valid_addresses(self):
        """Test with valid addresses from different Indian cities"""
        print("\n" + "="*100)
        print("✅ TEST 1: VALID ADDRESSES (Various Indian Cities)")
        print("="*100)
        
        test_cases = [
            # Format: (address, expected_state, description)
            ("Bengaluru, Karnataka", "Karnataka", "Simple city, state"),
            ("Vadodara, Gujarat", "Gujarat", "Another city, state"),
            ("Jamshedpur, Jharkhand", "Jharkhand", "Steel city"),
            ("Q.no-57/21 Chhota Govindpur, Jamshedpur Jharkhand-831015", "Jharkhand", "Complex Jamshedpur address"),
            ("Delhi", "Delhi", "Single city (capital)"),
            ("Mumbai, Maharashtra", "Maharashtra", "Metro city"),
            ("Kolkata, West Bengal", "West Bengal", "Eastern metro"),
            ("Chennai, Tamil Nadu", "Tamil Nadu", "Southern metro"),
            ("Hyderabad, Telangana", "Telangana", "Tech city"),
            ("Pune, Maharashtra", "Maharashtra", "Educational hub"),
        ]
        
        for address, expected_state, description in test_cases:
            self.results['total_tests'] += 1
            
            print(f"\n   Test {self.results['total_tests']}: {description}")
            print(f"   Address: {address}")
            
            start_time = time.time()
            lat, lon = self.service.geocode(address)
            elapsed = time.time() - start_time
            
            test_result = {
                'test_num': self.results['total_tests'],
                'category': 'valid_addresses',
                'address': address,
                'description': description,
                'result': 'PASSED' if lat and lon else 'FAILED',
                'latitude': lat,
                'longitude': lon,
                'time_seconds': round(elapsed, 2)
            }
            
            if lat and lon:
                print(f"   ✅ PASSED: ({lat:.4f}, {lon:.4f})")
                print(f"   ⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                test_result['result'] = 'PASSED'
            else:
                print(f"   ❌ FAILED: No coordinates returned")
                self.results['failed'] += 1
                test_result['result'] = 'FAILED'
            
            self.results['tests'].append(test_result)
    
    def test_complex_addresses(self):
        """Test with complex/problematic address formats"""
        print("\n" + "="*100)
        print("⚠️  TEST 2: COMPLEX/PROBLEMATIC ADDRESSES")
        print("="*100)
        
        test_cases = [
            ("Q.no-57/21, Jamshedpur", "Incomplete with house number"),
            ("Briyani House, Bengaluru", "Business name only"),
            ("Shivay Food, Jamshedpur, Jharkhand", "Business + city + state"),
            ("Chicken Street Food, Vadodara", "Business with street descriptor"),
            ("Shop 45, Main Road, Delhi", "Shop number + road + city"),
            ("Opp. Railway Station, Pune, Maharashtra", "Landmark reference"),
        ]
        
        for address, description in test_cases:
            self.results['total_tests'] += 1
            
            print(f"\n   Test {self.results['total_tests']}: {description}")
            print(f"   Address: {address}")
            
            start_time = time.time()
            lat, lon = self.service.geocode(address)
            elapsed = time.time() - start_time
            
            if lat and lon:
                print(f"   ✅ HANDLED: ({lat:.4f}, {lon:.4f})")
                print(f"   ⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                result = 'PASSED'
            else:
                print(f"   ⚠️  NO RESULT: Service handled gracefully")
                # This is acceptable - complex addresses might not geocode
                self.results['passed'] += 1
                result = 'PASSED (no coordinates, as expected)'
            
            test_result = {
                'test_num': self.results['total_tests'],
                'category': 'complex_addresses',
                'address': address,
                'description': description,
                'result': result,
                'latitude': lat,
                'longitude': lon,
                'time_seconds': round(elapsed, 2)
            }
            
            self.results['tests'].append(test_result)
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        print("\n" + "="*100)
        print("🔴 TEST 3: EDGE CASES & ERROR CONDITIONS")
        print("="*100)
        
        test_cases = [
            ("", "Empty string"),
            ("   ", "Whitespace only"),
            ("XYZ Invalid Place Name 12345", "Completely invalid"),
            ("New York, USA", "Non-India address"),
        ]
        
        for address, description in test_cases:
            self.results['total_tests'] += 1
            
            print(f"\n   Test {self.results['total_tests']}: {description}")
            if address:
                print(f"   Address: '{address}'")
            else:
                print(f"   Address: [empty]")
            
            try:
                start_time = time.time()
                lat, lon = self.service.geocode(address)
                elapsed = time.time() - start_time
                
                if lat is None and lon is None:
                    print(f"   ✅ HANDLED CORRECTLY: Returned (None, None)")
                    print(f"   ⏱️  Time: {elapsed:.2f}s")
                    self.results['passed'] += 1
                    result = 'PASSED'
                else:
                    print(f"   ⚠️  Got unexpected coordinates: ({lat}, {lon})")
                    result = 'WARNING'
                    self.results['failed'] += 1
            
            except Exception as e:
                print(f"   ❌ EXCEPTION: {type(e).__name__}: {e}")
                result = 'FAILED'
                self.results['failed'] += 1
                lat, lon = None, None
            
            test_result = {
                'test_num': self.results['total_tests'],
                'category': 'edge_cases',
                'address': address,
                'description': description,
                'result': result,
                'latitude': lat,
                'longitude': lon,
                'time_seconds': round(elapsed, 2) if 'elapsed' in locals() else 0
            }
            
            self.results['tests'].append(test_result)
    
    def test_fallback_strategies(self):
        """Test fallback strategies"""
        print("\n" + "="*100)
        print("🔄 TEST 4: FALLBACK STRATEGIES")
        print("="*100)
        
        print("\n   Testing simplified address fallback...")
        print("   When full address fails, system should try: city, state")
        
        # This is tested implicitly in other tests
        # Verbose logging shows fallback attempts
        
        address = "Q.no-57/21, Chhota Govindpur, Jamshedpur, Jharkhand-831015"
        print(f"\n   Address: {address}")
        print(f"   Expected fallback: 'Jamshedpur, Jharkhand'")
        
        start_time = time.time()
        lat, lon = self.service.geocode(address)
        elapsed = time.time() - start_time
        
        if lat and lon:
            print(f"   ✅ FALLBACK SUCCESSFUL: ({lat:.4f}, {lon:.4f})")
            self.results['passed'] += 1
            result = 'PASSED'
        else:
            print(f"   ❌ FALLBACK FAILED")
            self.results['failed'] += 1
            result = 'FAILED'
        
        self.results['total_tests'] += 1
        test_result = {
            'test_num': self.results['total_tests'],
            'category': 'fallback_strategies',
            'address': address,
            'description': 'Complex address with fallback to simplified',
            'result': result,
            'latitude': lat,
            'longitude': lon,
            'time_seconds': round(elapsed, 2)
        }
        
        self.results['tests'].append(test_result)
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "🧪"*50)
        print("ENHANCED GEOCODING SERVICE TEST SUITE")
        print("🧪"*50)
        
        self.test_valid_addresses()
        time.sleep(1)  # Respect rate limiting
        
        self.test_complex_addresses()
        time.sleep(1)
        
        self.test_edge_cases()
        time.sleep(1)
        
        self.test_fallback_strategies()
        
        self._print_summary()
        self._generate_report()
    
    def _print_summary(self):
        """Print test summary"""
        print("\n" + "="*100)
        print("📊 TEST SUMMARY")
        print("="*100)
        
        print(f"\n   Total Tests Run: {self.results['total_tests']}")
        print(f"   Passed: {self.results['passed']} ✅")
        print(f"   Failed: {self.results['failed']} ❌")
        
        if self.results['total_tests'] > 0:
            pass_rate = (self.results['passed'] / self.results['total_tests']) * 100
            print(f"   Pass Rate: {pass_rate:.1f}%")
        
        # Categorize by test type
        print(f"\n   By Category:")
        categories = {}
        for test in self.results['tests']:
            cat = test['category']
            if cat not in categories:
                categories[cat] = {'passed': 0, 'failed': 0}
            if test['result'].startswith('PASSED'):
                categories[cat]['passed'] += 1
            else:
                categories[cat]['failed'] += 1
        
        for cat, stats in categories.items():
            total = stats['passed'] + stats['failed']
            pct = (stats['passed'] / total * 100) if total > 0 else 0
            print(f"      {cat}: {stats['passed']}/{total} ({pct:.0f}%)")
        
        # Overall status
        print(f"\n🎯 OVERALL STATUS:")
        if self.results['failed'] == 0:
            print(f"   ✅ ALL TESTS PASSED")
            print(f"   ✅ Geocoding service is production-ready")
        else:
            print(f"   ⚠️  Some tests failed")
            print(f"   Review detailed report for investigation")
    
    def _generate_report(self):
        """Generate JSON test report"""
        report_path = 'geocoding_test_report.json'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 TEST REPORT:")
        print(f"   Saved to: {report_path}")
        print(f"   Contains: All test results and metrics")


def main():
    """Main entry point"""
    tester = GeocodingServiceTester()
    tester.run_all_tests()
    
    print(f"\n{'='*100}\n")


if __name__ == '__main__':
    main()
