#!/usr/bin/env python3
"""
Vendor Location Geocoding Diagnostics and Recovery Tool

This script helps diagnose and fix vendor location issues by:
1. Checking all vendors with missing coordinates
2. Attempting to re-geocode with the enhanced service
3. Providing detailed debugging information
4. Generating a comprehensive report
5. Offering recovery recommendations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.models import Vendor
from geocoding_enhanced import GeocodeServiceEnhanced
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

class VendorGeocodingDiagnostics:
    """Diagnose and fix vendor geocoding issues"""
    
    def __init__(self):
        self.service = GeocodeServiceEnhanced()
        self.results = {
            'total_vendors': 0,
            'missing_coordinates': 0,
            'already_geocoded': 0,
            're_geocoded_success': 0,
            're_geocoded_failed': 0,
            'vendors': []
        }
    
    def run_diagnostics(self):
        """Run full diagnostics"""
        print("\n" + "="*100)
        print("🔍 VENDOR LOCATION GEOCODING DIAGNOSTICS")
        print("="*100)
        
        with app.app_context():
            # Get all vendors
            all_vendors = Vendor.query.all()
            self.results['total_vendors'] = len(all_vendors)
            
            print(f"\n📊 SCAN RESULTS:")
            print(f"   Total vendors in database: {len(all_vendors)}")
            
            if not all_vendors:
                print(f"   ⚠️  No vendors found in database")
                return
            
            # Categorize vendors
            missing_coords = []
            has_coords = []
            
            for vendor in all_vendors:
                if not vendor.latitude or not vendor.longitude:
                    missing_coords.append(vendor)
                else:
                    has_coords.append(vendor)
            
            self.results['missing_coordinates'] = len(missing_coords)
            self.results['already_geocoded'] = len(has_coords)
            
            print(f"   ✅ Vendors with coordinates: {len(has_coords)}")
            print(f"   ❌ Vendors missing coordinates: {len(missing_coords)}")
            
            # Display vendors with coordinates
            if has_coords:
                print(f"\n{'─'*100}")
                print(f"✅ VENDORS WITH COORDINATES (Already Geocoded)")
                print(f"{'─'*100}")
                
                for vendor in has_coords:
                    print(f"\n   ID: {vendor.id}")
                    print(f"   Name: {vendor.business_name}")
                    print(f"   Address: {vendor.business_address}")
                    print(f"   Coordinates: ({vendor.latitude:.4f}, {vendor.longitude:.4f})")
                    
                    self.results['vendors'].append({
                        'id': vendor.id,
                        'name': vendor.business_name,
                        'address': vendor.business_address,
                        'latitude': vendor.latitude,
                        'longitude': vendor.longitude,
                        'status': 'already_geocoded'
                    })
            
            # Attempt to re-geocode vendors missing coordinates
            if missing_coords:
                print(f"\n{'─'*100}")
                print(f"🔄 ATTEMPTING TO RE-GEOCODE MISSING COORDINATES")
                print(f"{'─'*100}")
                
                for idx, vendor in enumerate(missing_coords, 1):
                    print(f"\n[{idx}/{len(missing_coords)}] Vendor: {vendor.business_name}")
                    print(f"     ID: {vendor.id}")
                    print(f"     Address: {vendor.business_address}")
                    
                    # Attempt geocoding
                    print(f"     Geocoding in progress...")
                    lat, lon = self.service.geocode(vendor.business_address)
                    
                    if lat and lon:
                        # Update database
                        vendor.latitude = lat
                        vendor.longitude = lon
                        db.session.commit()
                        
                        print(f"     ✅ SUCCESS: Coordinates saved ({lat:.4f}, {lon:.4f})")
                        self.results['re_geocoded_success'] += 1
                        
                        self.results['vendors'].append({
                            'id': vendor.id,
                            'name': vendor.business_name,
                            'address': vendor.business_address,
                            'latitude': lat,
                            'longitude': lon,
                            'status': 're_geocoded_success'
                        })
                    else:
                        print(f"     ❌ FAILED: Could not determine coordinates")
                        self.results['re_geocoded_failed'] += 1
                        
                        self.results['vendors'].append({
                            'id': vendor.id,
                            'name': vendor.business_name,
                            'address': vendor.business_address,
                            'latitude': None,
                            'longitude': None,
                            'status': 're_geocoded_failed',
                            'reason': 'Address geocoding failed - try a more complete address with city and state'
                        })
            
            # Summary
            self._print_summary()
            self._generate_report()
    
    def _print_summary(self):
        """Print diagnostics summary"""
        print(f"\n{'='*100}")
        print(f"📋 DIAGNOSTICS SUMMARY")
        print(f"{'='*100}")
        
        print(f"\n   Total Vendors: {self.results['total_vendors']}")
        print(f"   Already Geocoded: {self.results['already_geocoded']}")
        print(f"   Re-geocoded (Success): {self.results['re_geocoded_success']}")
        print(f"   Re-geocoded (Failed): {self.results['re_geocoded_failed']}")
        print(f"   Still Missing Coordinates: {self.results['missing_coordinates'] - self.results['re_geocoded_success']}")
        
        # Success rate
        total_attempted = self.results['re_geocoded_success'] + self.results['re_geocoded_failed']
        if total_attempted > 0:
            success_rate = (self.results['re_geocoded_success'] / total_attempted) * 100
            print(f"   Re-geocoding Success Rate: {success_rate:.1f}%")
        
        # Status
        print(f"\n🎯 STATUS:")
        if self.results['missing_coordinates'] == 0:
            print(f"   ✅ All vendors have coordinates!")
            print(f"   ✅ Map feature should work for all vendors")
        elif self.results['missing_coordinates'] - self.results['re_geocoded_success'] == 0:
            print(f"   ✅ All missing coordinates recovered!")
            print(f"   ✅ All vendors now appear on map")
        else:
            remaining = self.results['missing_coordinates'] - self.results['re_geocoded_success']
            print(f"   ⚠️  {remaining} vendors still missing coordinates")
            print(f"   💡 These vendors may have incomplete addresses")
            print(f"   💡 Manual address updates may be needed")
    
    def _generate_report(self):
        """Generate detailed JSON report"""
        report_path = 'geocoding_diagnostics_report.json'
        
        self.results['timestamp'] = datetime.now().isoformat()
        self.results['report_file'] = report_path
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 DETAILED REPORT:")
        print(f"   Saved to: {report_path}")
        print(f"   Use this for further analysis or debugging")
    
    def fix_addresses_interactively(self):
        """Allow manual address correction"""
        with app.app_context():
            missing = Vendor.query.filter(
                (Vendor.latitude.is_(None)) | (Vendor.longitude.is_(None))
            ).all()
            
            if not missing:
                print("\n✅ All vendors have coordinates!")
                return
            
            print(f"\n{'─'*100}")
            print(f"🔧 INTERACTIVE ADDRESS CORRECTION")
            print(f"{'─'*100}")
            
            for vendor in missing:
                print(f"\n📍 Vendor: {vendor.business_name}")
                print(f"   Current Address: {vendor.business_address}")
                print(f"   Current Coords: {vendor.latitude}, {vendor.longitude}")
                
                choice = input(f"\n   Enter new address (or press Enter to skip): ").strip()
                
                if choice:
                    print(f"   Geocoding new address...")
                    lat, lon = self.service.geocode(choice)
                    
                    if lat and lon:
                        vendor.business_address = choice
                        vendor.latitude = lat
                        vendor.longitude = lon
                        db.session.commit()
                        
                        print(f"   ✅ Saved: ({lat:.4f}, {lon:.4f})")
                    else:
                        print(f"   ❌ Could not geocode address")
    
    def export_vendor_locations(self):
        """Export all vendor locations to CSV"""
        import csv
        
        csv_path = 'vendor_locations_export.csv'
        
        with app.app_context():
            vendors = Vendor.query.all()
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Business Name', 'Address', 'Latitude', 'Longitude', 'Status'])
                
                for vendor in vendors:
                    status = 'Geocoded' if vendor.latitude and vendor.longitude else 'Missing'
                    writer.writerow([
                        vendor.id,
                        vendor.business_name,
                        vendor.business_address,
                        vendor.latitude or '',
                        vendor.longitude or '',
                        status
                    ])
        
        print(f"\n📊 EXPORT COMPLETE")
        print(f"   File: {csv_path}")
        print(f"   Contains: All vendor locations")


def main():
    """Main entry point"""
    print("\n" + "🌍"*50)
    print("VENDOR LOCATION GEOCODING DIAGNOSTICS & RECOVERY")
    print("🌍"*50)
    
    diagnostics = VendorGeocodingDiagnostics()
    
    # Run full diagnostics
    diagnostics.run_diagnostics()
    
    # Ask for additional actions
    print(f"\n{'─'*100}")
    print("OPTIONS:")
    print("  1. Exit")
    print("  2. Manually correct addresses")
    print("  3. Export vendor locations to CSV")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '2':
        diagnostics.fix_addresses_interactively()
    elif choice == '3':
        diagnostics.export_vendor_locations()
    
    print(f"\n✅ Diagnostics complete")
    print(f"{'═'*100}\n")


if __name__ == '__main__':
    main()
