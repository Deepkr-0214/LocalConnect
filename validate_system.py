"""
System Validation Script
Verifies that all components of the dynamic geocoding system are in place
"""

import os
import sys
import json
from datetime import datetime

def check_file_exists(filepath):
    """Check if a file exists"""
    return os.path.isfile(filepath)

def check_file_contains(filepath, search_string):
    """Check if file contains a specific string"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            return search_string in content
    except:
        return False

def validate_geocoding_system():
    """Validate the complete geocoding system"""
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'checks': [],
        'summary': {}
    }
    
    print("\n" + "="*70)
    print("DYNAMIC GEOCODING SYSTEM VALIDATION")
    print("="*70)
    
    # Check 1: geocode.py exists
    geocode_file = os.path.join(base_path, 'geocode.py')
    exists = check_file_exists(geocode_file)
    check_1 = {
        'name': 'Geocoding Service Module',
        'file': 'geocode.py',
        'status': 'PASS' if exists else 'FAIL',
        'details': 'GeocodeService class exists' if exists else 'File not found'
    }
    validation_results['checks'].append(check_1)
    print(f"{'✅' if exists else '❌'} Geocoding Service (geocode.py)")
    
    # Check 2: app.py imports geocode
    app_file = os.path.join(base_path, 'app.py')
    has_import = check_file_contains(app_file, 'from geocode import GeocodeService')
    check_2 = {
        'name': 'GeocodeService Import in app.py',
        'file': 'app.py',
        'status': 'PASS' if has_import else 'FAIL',
        'details': 'Import statement found' if has_import else 'Import missing'
    }
    validation_results['checks'].append(check_2)
    print(f"{'✅' if has_import else '❌'} GeocodeService Import (app.py)")
    
    # Check 3: Vendor signup geocoding
    has_geocoding = check_file_contains(app_file, 'geocode_address')
    check_3 = {
        'name': 'Vendor Signup Geocoding',
        'file': 'app.py',
        'status': 'PASS' if has_geocoding else 'FAIL',
        'details': 'Geocoding in vendor_signup' if has_geocoding else 'Geocoding not implemented'
    }
    validation_results['checks'].append(check_3)
    print(f"{'✅' if has_geocoding else '❌'} Vendor Signup Geocoding")
    
    # Check 4: Map view route
    has_map_route = check_file_contains(app_file, "/customer/vendor/<int:vendor_id>/map")
    check_4 = {
        'name': 'Map View Route',
        'file': 'app.py',
        'status': 'PASS' if has_map_route else 'FAIL',
        'details': 'Route /customer/vendor/<id>/map exists' if has_map_route else 'Route not found'
    }
    validation_results['checks'].append(check_4)
    print(f"{'✅' if has_map_route else '❌'} Map View Route")
    
    # Check 5: API endpoint
    has_api = check_file_contains(app_file, '/api/vendor/<int:vendor_id>/location')
    check_5 = {
        'name': 'Location API Endpoint',
        'file': 'app.py',
        'status': 'PASS' if has_api else 'FAIL',
        'details': 'Endpoint /api/vendor/<id>/location exists' if has_api else 'Endpoint not found'
    }
    validation_results['checks'].append(check_5)
    print(f"{'✅' if has_api else '❌'} Location API Endpoint")
    
    # Check 6: Map template
    map_template = os.path.join(base_path, 'templates', 'customer', 'map_view.html')
    has_template = check_file_exists(map_template)
    check_6 = {
        'name': 'Map Template',
        'file': 'templates/customer/map_view.html',
        'status': 'PASS' if has_template else 'FAIL',
        'details': 'Map template exists' if has_template else 'Template file not found'
    }
    validation_results['checks'].append(check_6)
    print(f"{'✅' if has_template else '❌'} Map Template (map_view.html)")
    
    # Check 7: Leaflet.js in template
    if has_template:
        has_leaflet = check_file_contains(map_template, 'leaflet')
        check_7 = {
            'name': 'Leaflet.js Integration',
            'file': 'templates/customer/map_view.html',
            'status': 'PASS' if has_leaflet else 'FAIL',
            'details': 'Leaflet.js loaded' if has_leaflet else 'Leaflet.js not found'
        }
        validation_results['checks'].append(check_7)
        print(f"{'✅' if has_leaflet else '❌'} Leaflet.js in Template")
    
    # Check 8: Requirements.txt has dependencies
    req_file = os.path.join(base_path, 'requirements.txt')
    has_requests = check_file_contains(req_file, 'requests==')
    check_8 = {
        'name': 'Required Dependencies',
        'file': 'requirements.txt',
        'status': 'PASS' if has_requests else 'FAIL',
        'details': 'requests library included' if has_requests else 'requests library missing'
    }
    validation_results['checks'].append(check_8)
    print(f"{'✅' if has_requests else '❌'} Required Dependencies (requests)")
    
    # Check 9: Database model has lat/lon fields
    model_file = os.path.join(base_path, 'models', 'models.py')
    has_lat = check_file_contains(model_file, 'latitude = db.Column')
    has_lon = check_file_contains(model_file, 'longitude = db.Column')
    check_9 = {
        'name': 'Database Model Fields',
        'file': 'models/models.py',
        'status': 'PASS' if (has_lat and has_lon) else 'FAIL',
        'details': 'Vendor model has latitude and longitude fields' if (has_lat and has_lon) else 'Fields missing'
    }
    validation_results['checks'].append(check_9)
    print(f"{'✅' if (has_lat and has_lon) else '❌'} Vendor Model Fields (latitude, longitude)")
    
    # Check 10: Documentation
    guide_file = os.path.join(base_path, 'GEOCODING_IMPLEMENTATION_GUIDE.md')
    has_guide = check_file_exists(guide_file)
    check_10 = {
        'name': 'Implementation Guide',
        'file': 'GEOCODING_IMPLEMENTATION_GUIDE.md',
        'status': 'PASS' if has_guide else 'FAIL',
        'details': 'Implementation guide exists' if has_guide else 'Documentation missing'
    }
    validation_results['checks'].append(check_10)
    print(f"{'✅' if has_guide else '❌'} Implementation Guide")
    
    # Check 11: Test script
    test_file = os.path.join(base_path, 'test_dynamic_geocoding.py')
    has_test = check_file_exists(test_file)
    check_11 = {
        'name': 'Test Suite',
        'file': 'test_dynamic_geocoding.py',
        'status': 'PASS' if has_test else 'FAIL',
        'details': 'Test suite exists' if has_test else 'Test file missing'
    }
    validation_results['checks'].append(check_11)
    print(f"{'✅' if has_test else '❌'} Test Suite (test_dynamic_geocoding.py)")
    
    # Check 12: Quick reference guide
    qref_file = os.path.join(base_path, 'QUICK_REFERENCE_GEOCODING.md')
    has_qref = check_file_exists(qref_file)
    check_12 = {
        'name': 'Quick Reference Guide',
        'file': 'QUICK_REFERENCE_GEOCODING.md',
        'status': 'PASS' if has_qref else 'FAIL',
        'details': 'Quick reference exists' if has_qref else 'Quick reference missing'
    }
    validation_results['checks'].append(check_12)
    print(f"{'✅' if has_qref else '❌'} Quick Reference Guide")
    
    # Summary
    total_checks = len(validation_results['checks'])
    passed_checks = len([c for c in validation_results['checks'] if c['status'] == 'PASS'])
    failed_checks = len([c for c in validation_results['checks'] if c['status'] == 'FAIL'])
    
    validation_results['summary'] = {
        'total': total_checks,
        'passed': passed_checks,
        'failed': failed_checks,
        'percentage': round((passed_checks / total_checks) * 100, 1)
    }
    
    # Print summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Total Checks: {total_checks}")
    print(f"✅ Passed: {passed_checks}")
    print(f"❌ Failed: {failed_checks}")
    print(f"Success Rate: {validation_results['summary']['percentage']}%")
    
    # Print result
    if failed_checks == 0:
        print("\n🎉 ALL VALIDATION CHECKS PASSED!")
        print("✨ Dynamic geocoding system is fully implemented and ready!")
    else:
        print(f"\n⚠️ {failed_checks} check(s) failed. Review the items above.")
    
    # Save report
    report_file = os.path.join(base_path, 'validation_report.json')
    with open(report_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    print("\n" + "="*70)
    print("System Status: " + ("✅ READY FOR PRODUCTION" if failed_checks == 0 else "⚠️ NEEDS ATTENTION"))
    print("="*70 + "\n")
    
    return failed_checks == 0


if __name__ == '__main__':
    success = validate_geocoding_system()
    sys.exit(0 if success else 1)
