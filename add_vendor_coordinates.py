import sqlite3
import os
from geocode import GeocodeService
from geocode import GeocodeService

# Initialize geocode service
geocode_service = GeocodeService()

def add_sample_coordinates():
    """Add geocoded coordinates to existing vendors based on their address"""
    db_path = os.path.join(os.getcwd(), "instance", "database.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all vendors with their address
    cursor.execute("SELECT id, business_name, business_address FROM vendor")
    vendors = cursor.fetchall()

    if not vendors:
        print("No vendors found in database")
        conn.close()
        return

    print(f"Found {len(vendors)} vendors. Geocoding addresses...")

    successful = 0
    failed = 0

    for vendor_id, business_name, business_address in vendors:
        # Use vendor's address to get coordinates
        if not business_address:
            print(f"⚠️  {business_name} - No address provided, skipping...")
            failed += 1
            continue
        
        print(f"🔍 Geocoding: {business_name} ({business_address})")
        vendor_lat, vendor_lon = geocode_service.get_coordinates(business_address)
        
        if vendor_lat is None or vendor_lon is None:
            print(f"❌ Location not available for {business_name}")
            failed += 1
            continue

        cursor.execute(
            "UPDATE vendor SET latitude = ?, longitude = ? WHERE id = ?",
            (vendor_lat, vendor_lon, vendor_id)
        )
        print(f"✅ Updated {business_name} - Lat: {vendor_lat:.4f}, Lon: {vendor_lon:.4f}")
        successful += 1

    conn.commit()
    conn.close()
    print(f"\n✨ Geocoding Complete!")
    print(f"✅ Successfully geocoded: {successful} vendors")
    print(f"❌ Failed: {failed} vendors")

if __name__ == "__main__":
    add_sample_coordinates()
