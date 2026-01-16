import sqlite3
import os
import random

def add_sample_coordinates():
    """Add sample coordinates to existing vendors (Delhi NCR area)"""
    db_path = os.path.join(os.getcwd(), "instance", "database.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all vendors
    cursor.execute("SELECT id, business_name FROM vendor")
    vendors = cursor.fetchall()

    if not vendors:
        print("No vendors found in database")
        conn.close()
        return

    # Delhi NCR base coordinates (around Connaught Place)
    base_lat = 28.6139
    base_lon = 77.2090

    print(f"Found {len(vendors)} vendors. Adding sample coordinates...")

    for vendor_id, business_name in vendors:
        # Generate random coordinates within ~10km radius of Delhi center
        # Roughly 0.1 degree = ~11km
        lat_offset = random.uniform(-0.09, 0.09)
        lon_offset = random.uniform(-0.09, 0.09)
        
        vendor_lat = base_lat + lat_offset
        vendor_lon = base_lon + lon_offset

        cursor.execute(
            "UPDATE vendor SET latitude = ?, longitude = ? WHERE id = ?",
            (vendor_lat, vendor_lon, vendor_id)
        )
        print(f"Updated {business_name} - Lat: {vendor_lat:.4f}, Lon: {vendor_lon:.4f}")

    conn.commit()
    conn.close()
    print("\nSuccessfully added coordinates to all vendors!")

if __name__ == "__main__":
    add_sample_coordinates()
