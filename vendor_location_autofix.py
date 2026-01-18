"""
Automatic Vendor Location Fixer
Runs automatically to geocode all vendors with missing coordinates
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import will be deferred to avoid circular imports
import logging

logger = logging.getLogger(__name__)

class VendorLocationAutoFixer:
    """Automatically fix missing vendor coordinates"""
    
    def __init__(self, app, db, Vendor, GeocodeServiceEnhanced):
        self.app = app
        self.db = db
        self.Vendor = Vendor
        self.service = GeocodeServiceEnhanced()
        self.fixed_count = 0
        self.failed_count = 0
        self.already_had_coords = 0
    
    def fix_all_vendors(self):
        """Fix all vendors with missing coordinates"""
        
        print("\n" + "="*100)
        print("🔧 AUTO-FIXING VENDOR LOCATIONS")
        print("="*100)
        
        with self.app.app_context():
            # Get all vendors
            all_vendors = self.Vendor.query.all()
            total = len(all_vendors)
            
            print(f"\n📊 SCAN RESULTS:")
            print(f"   Total vendors: {total}")
            
            # Separate vendors with and without coordinates
            missing_coords = [v for v in all_vendors if not v.latitude or not v.longitude]
            has_coords = [v for v in all_vendors if v.latitude and v.longitude]
            
            self.already_had_coords = len(has_coords)
            
            print(f"   ✅ Already have coordinates: {len(has_coords)}")
            print(f"   ❌ Missing coordinates: {len(missing_coords)}")
            
            if not missing_coords:
                print(f"\n✅ All vendors already have coordinates!")
                print("="*100 + "\n")
                return
            
            # Fix vendors with missing coordinates
            print(f"\n🔄 AUTO-FIXING MISSING COORDINATES...")
            print(f"{'─'*100}")
            
            for idx, vendor in enumerate(missing_coords, 1):
                print(f"\n[{idx}/{len(missing_coords)}] {vendor.business_name}")
                print(f"   Address: {vendor.business_address}")
                
                # Attempt geocoding
                lat, lon = self.service.geocode(vendor.business_address)
                
                if lat and lon:
                    # Save to database
                    vendor.latitude = lat
                    vendor.longitude = lon
                    self.db.session.commit()
                    
                    print(f"   ✅ FIXED: ({lat:.4f}, {lon:.4f})")
                    self.fixed_count += 1
                else:
                    print(f"   ❌ FAILED: Could not geocode")
                    print(f"      Suggestion: Update address to include city and state")
                    self.failed_count += 1
            
            # Print summary
            self._print_summary()
    
    def _print_summary(self):
        """Print summary of fixes"""
        total_fixed = self.fixed_count + self.already_had_coords
        total_vendors = total_fixed + self.failed_count
        
        print(f"\n{'='*100}")
        print(f"📈 SUMMARY")
        print(f"{'='*100}")
        
        print(f"\n   ✅ Already had coordinates: {self.already_had_coords}")
        print(f"   ✅ Auto-fixed: {self.fixed_count}")
        print(f"   ❌ Could not fix: {self.failed_count}")
        print(f"   ─────────────────────────")
        print(f"   ✅ Total with coordinates: {total_fixed}/{total_vendors}")
        
        if self.failed_count > 0:
            print(f"\n   💡 NOTE: {self.failed_count} vendors still need manual address updates")
            print(f"   💡 Use better format: 'Business Name, City, State'")
        
        if total_fixed == total_vendors:
            print(f"\n   🎉 ALL VENDORS NOW HAVE COORDINATES!")
            print(f"   🗺️  All vendors will appear on customer maps")
        
        print(f"\n{'='*100}\n")


def auto_fix_on_startup(app, db, Vendor, GeocodeServiceEnhanced):
    """Auto-fix vendor locations when server starts"""
    print("\n" + "🚀"*50)
    print("VENDOR LOCATION AUTO-FIX RUNNING")
    print("🚀"*50)
    
    fixer = VendorLocationAutoFixer(app, db, Vendor, GeocodeServiceEnhanced)
    fixer.fix_all_vendors()


if __name__ == '__main__':
    # For standalone testing - will fail without proper imports
    print("This module should be called from app.py during initialization")
