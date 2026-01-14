import os
import json
import time
import requests
import pandas as pd
import geopandas as gpd
import osmnx as ox
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon
from sqlalchemy import text
from datetime import datetime
from dotenv import load_dotenv

from pipelines.second_step__syncer import sync_data_to_main_table
from config.database import SessionLocal


load_dotenv()

# --- CẤU HÌNH ---
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Thiếu GOOGLE_MAPS_API_KEY trong file .env")

# Khoảng cách giữa các điểm quét (độ). 0.01 độ ~ 1.1km
# Google Places Nearby search radius thường là 750m-1000m. 
# Grid step 0.012 (~1.3km) + Radius 800m sẽ phủ kín mà ít trùng lặp lớn.
GRID_STEP = 0.012 
SCAN_RADIUS = 800 

DISTRICTS = [
    "Thủ Đức, Ho Chi Minh City, Vietnam",
    "District 1, Ho Chi Minh City, Vietnam",
    "District 2, Ho Chi Minh City, Vietnam",
    "District 3, Ho Chi Minh City, Vietnam",
    "District 4, Ho Chi Minh City, Vietnam",
    "District 5, Ho Chi Minh City, Vietnam",
    "District 6, Ho Chi Minh City, Vietnam",
    "District 7, Ho Chi Minh City, Vietnam",
    "District 8, Ho Chi Minh City, Vietnam",
    "District 10, Ho Chi Minh City, Vietnam",
    "District 11, Ho Chi Minh City, Vietnam",
    "District 12, Ho Chi Minh City, Vietnam",
    "Binh Tan District, Ho Chi Minh City, Vietnam",
    "Binh Thanh District, Ho Chi Minh City, Vietnam",
    "Go Vap District, Ho Chi Minh City, Vietnam",
    "Phu Nhuan District, Ho Chi Minh City, Vietnam",
    "Tan Binh District, Ho Chi Minh City, Vietnam",
    "Tan Phu District, Ho Chi Minh City, Vietnam",
    "Binh Chanh District, Ho Chi Minh City, Vietnam",
    "Can Gio District, Ho Chi Minh City, Vietnam",
    "Cu Chi District, Ho Chi Minh City, Vietnam",
    "Hoc Mon District, Ho Chi Minh City, Vietnam",
    "Nha Be District, Ho Chi Minh City, Vietnam"
]

# Mapping Category của dự án sang Google Place Types
# Sử dụng API v1 (New Places API) types
CATEGORY_TO_GOOGLE_TYPE = {
    'healthcare': ['hospital', 'pharmacy', 'doctor', 'chiropractor', 'dental_clinic', 'veterinary_care', 'dentist', 'drugstore', 'massage'],
    'education': ['school', 'university', 'primary_school', 'secondary_school', 'preschool', 'library'],
    'shopping': ['supermarket', 'shopping_mall', 'convenience_store', 'market', 'department_store', 'book_store', 'clothing_store', 'electronics_store', 'hardware_store', 'furniture_store', 'store'],
    'transportation': ['bus_station', 'train_station', 'subway_station', 'airport', 'taxi_stand', 'ferry_terminal'],
    'environment': ['park', 'tourist_attraction', 'zoo', 'aquarium', 'botanical_garden'],
    'entertainment': ['restaurant', 'cafe', 'bar', 'night_club', 'movie_theater', 'museum', 'art_gallery', 'amusement_park', 'stadium', 'performing_arts_theater'],
    'public_safety': ['police', 'fire_station', 'post_office', 'city_hall', 'courthouse']
}

def get_district_boundary(district_name):
    """Lấy Polygon ranh giới quận từ OSM"""
    try:
        gdf = ox.geocode_to_gdf(district_name)
        return gdf.iloc[0].geometry
    except Exception as e:
        print(f"Error fetching boundary for {district_name}: {e}")
        return None

def generate_scan_points(polygon):
    """Tạo lưới điểm quét nằm trong Polygon"""
    minx, miny, maxx, maxy = polygon.bounds
    
    x_coords = np.arange(minx, maxx, GRID_STEP)
    y_coords = np.arange(miny, maxy, GRID_STEP)
    
    points = []
    for x in x_coords:
        for y in y_coords:
            p = Point(x, y)
            if polygon.contains(p): # Chỉ lấy điểm nằm trong quận
                points.append(p)
    return points

def fetch_google_places(lat, lng, types, run_id, category, district_name, db):
    """Gọi Google Places API New (v1)"""
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        # Chỉ lấy các trường cần thiết để tiết kiệm và nhẹ payload
        "X-Goog-FieldMask": "places.id,places.displayName,places.types,places.rating,places.userRatingCount,places.location,places.formattedAddress"
    }
    
    body = {
        "includedTypes": types,
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": SCAN_RADIUS
            }
        },
        "languageCode": "vi"
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code != 200:
            print(f"    ! API Error: {response.status_code} - {response.text}")
            return 0

        data = response.json()
        places = data.get('places', [])
        
        if not places: return 0

        insert_values = []
        for p in places:
            loc = p.get('location', {})
            lat_p = loc.get('latitude')
            lng_p = loc.get('longitude')
            name = p.get('displayName', {}).get('text')
            
            if not name or not lat_p or not lng_p: continue

            wkt_point = f"SRID=4326;POINT({lng_p} {lat_p})"
            
            insert_values.append({
                "run_id": run_id,
                "name": name,
                "category": category,
                "district": district_name.split(',')[0],
                "amenity_type": p.get('types', [])[0] if p.get('types') else 'unknown',
                "longitude": lng_p,
                "latitude": lat_p,
                "google_place_id": p.get('id'),
                "google_rating": p.get('rating'),
                "google_user_ratings_total": p.get('userRatingCount'),
                "google_types": json.dumps(p.get('types', [])),
                "vicinity": p.get('formattedAddress'),
                "all_tags": json.dumps(p),
                "location": wkt_point
            })

        if insert_values:
            # Insert vào bảng RAW
            sql = text("""
                INSERT INTO google_raw_amenities 
                (run_id, name, category, district, amenity_type, longitude, latitude, 
                 google_place_id, google_rating, google_user_ratings_total, google_types, vicinity, all_tags, location)
                VALUES (:run_id, :name, :category, :district, :amenity_type, :longitude, :latitude,
                        :google_place_id, :google_rating, :google_user_ratings_total, :google_types, :vicinity, :all_tags, :location)
            """)
            db.execute(sql, insert_values)
            db.commit()
            return len(insert_values)
            
    except Exception as e:
        print(f"    ! Exception: {e}")
        return 0
    
    return 0

def run_seed():
    print("\n========================================================")
    print("   BẮT ĐẦU GOOGLE MAPS SEEDING (FULL COVERAGE)")
    print("========================================================\n")
    
    db = SessionLocal()
    
    try:
        # 1. Tạo Run ID mới
        result = db.execute(text("INSERT INTO run_collection_amenities DEFAULT VALUES RETURNING id"))
        run_id = result.scalar()
        db.commit()
        print(f"=== INITIAL RUN ID: {run_id} ===")

        total_collected = 0

        # 2. Duyệt từng Quận
        for district in DISTRICTS:
            short_name = district.split(',')[0]
            print(f"\n>>> Đang xử lý: {short_name}")
            
            # Lấy hình dáng quận
            boundary = get_district_boundary(district)
            if not boundary:
                print("    ! Không lấy được boundary, bỏ qua.")
                continue
                
            # Tạo lưới điểm quét
            scan_points = generate_scan_points(boundary)
            print(f"    -> Đã tạo {len(scan_points)} điểm quét phủ kín quận.")
            
            # 3. Duyệt từng loại Amenities
            for category, types in CATEGORY_TO_GOOGLE_TYPE.items():
                print(f"    -> Quét danh mục: {category}...")
                count_cat = 0
                
                # Duyệt từng điểm quét
                for i, point in enumerate(scan_points):
                    saved = fetch_google_places(point.y, point.x, types, run_id, category, district, db)
                    count_cat += saved
                    
                    # Log tiến độ nhẹ
                    # if (i+1) % 5 == 0: print(f"       . Progress {i+1}/{len(scan_points)}")
                    
                    time.sleep(0.2) # Delay nhẹ tránh rate limit quá gắt
                
                print(f"       + Đã thu thập {count_cat} địa điểm {category}.")
                total_collected += count_cat

        print(f"\n========================================================")
        print(f"   SEED HOÀN TẤT. TỔNG CỘNG: {total_collected} ĐỊA ĐIỂM")
        print("========================================================")
        
        # 4. Trigger Sync (Tùy chọn: gọi pipeline sync để đẩy sang bảng chính)
        print("Đang đồng bộ sang bảng chính Amenities...")
        sync_data_to_main_table(run_id, db)
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("Bắt đầu script")
    if confirm.lower() == 'y':
        run_seed()
    else:
        print("Đã hủy.")