import osmnx as ox
import pandas as pd
import json
import time
from sqlalchemy import text
from shapely import wkt

# Cấu hình danh sách quận và tag (như code cũ của bạn)
DISTRICTS = [
    # City
    "Thủ Đức",

    # Urban Districts
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

    # Rural Districts
    "Binh Chanh District, Ho Chi Minh City, Vietnam",
    "Can Gio District, Ho Chi Minh City, Vietnam",
    "Cu Chi District, Ho Chi Minh City, Vietnam",
    "Hoc Mon District, Ho Chi Minh City, Vietnam",
    "Nha Be District, Ho Chi Minh City, Vietnam"
]

TAGS = {
    # 🏥 Sức khỏe & Y tế
    "healthcare": {
        "amenity": ["hospital", "clinic", "doctors", "dentist", "pharmacy", "veterinary", "nursing_home"]
    },
    # 🎓 Giáo dục
    "education": {
        "amenity": ["school", "kindergarten", "university", "college", "library", "language_school", "driving_school"]
    },
    # 🛍️ Mua sắm
    "shopping": {
        "shop": [
            "supermarket", "convenience", "mall", "department_store", 
            "clothes", "bakery", "butcher", "electronics", "books", 
            "hardware", "furniture"
        ],
        "amenity": ["marketplace", "vending_machine"]
    },        
    # 🚌 Giao thông
    "transportation": {
        "highway": ["bus_stop", "traffic_signals"],
        "public_transport": ["station", "stop_position", "platform"],
        "amenity": ["parking", "bicycle_parking", "bicycle_rental", "fuel", "taxi", "ferry_terminal"],
        "railway": ["station", "subway_entrance", "tram_stop"],
        "aeroway": ["airport", "helipad"]
    },
    # 🌳 Môi trường & Giải trí ngoài trời
    "environment": {
        "leisure": [
            "park", "garden", "playground", "sports_centre", "stadium", 
            "swimming_pool", "nature_reserve", "dog_park", "pitch"
        ],
        "natural": ["water", "beach", "wood", "tree"]
    },
    # 🎭 Văn hóa & Giải trí
    "entertainment": {
        "amenity": [
            "cafe", "restaurant", "fast_food", "food_court", "bar", "pub", 
            "nightclub", "cinema", "theatre", "community_centre", "arts_centre"
        ],
        "tourism": ["museum", "gallery", "artwork", "attraction", "viewpoint"],
        "historic": ["monument", "memorial"]
    },
    # 🏛️ Dịch vụ công & An ninh
    "public_safety": {
        "amenity": ["police", "fire_station", "post_office", "townhall", "courthouse"],
        "emergency": ["phone", "ambulance_station"]
    },
}

def run_osm_pipeline(run_id, db_session):
    print(f"--- [OSM] Bắt đầu thu thập cho Run ID: {run_id} ---")
    
    total_inserted = 0

    for category, category_tags in TAGS.items():
        for district_name in DISTRICTS:
            try:
                # 1. Lấy dữ liệu từ OSM
                gdf = ox.features_from_place(district_name, category_tags)
                if gdf.empty:
                    continue

                # 2. Xử lý dữ liệu
                # Lấy centroid cho các polygon
                gdf['geometry'] = gdf.geometry.centroid
                gdf['longitude'] = gdf.geometry.x
                gdf['latitude'] = gdf.geometry.y
                
                # Xác định amenity_type
                type_cols = list(category_tags.keys())
                existing_cols = [c for c in type_cols if c in gdf.columns]
                if existing_cols:
                    gdf['amenity_type'] = gdf[existing_cols].bfill(axis=1).iloc[:, 0]
                else:
                    gdf['amenity_type'] = 'unknown'

                # Tạo all_tags JSON
                non_tag_cols = ['geometry', 'osmid', 'element_type', 'nodes', 'amenity_type', 'longitude', 'latitude']
                gdf['all_tags'] = gdf.apply(
                    lambda row: json.dumps(
                        row.drop(labels=non_tag_cols, errors='ignore').dropna().to_dict(), 
                        ensure_ascii=False
                    ), axis=1
                )

                # 3. Insert vào DB (Batch Insert)
                # Chuẩn bị list dict để insert nhanh
                clean_district = district_name.split(',')[0]
                
                insert_values = []
                for _, row in gdf.iterrows():
                    # Format WKT Point cho PostGIS
                    wkt_point = f"SRID=4326;POINT({row['longitude']} {row['latitude']})"
                    
                    insert_values.append({
                        "run_id": run_id,
                        "name": str(row.get('name', 'Unnamed')),
                        "category": category,
                        "district": clean_district,
                        "amenity_type": str(row.get('amenity_type', '')),
                        "longitude": row['longitude'],
                        "latitude": row['latitude'],
                        "all_tags": row['all_tags'],
                        "location": wkt_point
                    })

                if insert_values:
                    # Sử dụng SQL thuần để insert batch cho nhanh
                    sql = text("""
                        INSERT INTO osm_raw_amenities 
                        (run_id, name, category, district, amenity_type, longitude, latitude, all_tags, location)
                        VALUES (:run_id, :name, :category, :district, :amenity_type, :longitude, :latitude, :all_tags, :location)
                    """)
                    db_session.execute(sql, insert_values)
                    db_session.commit()
                    total_inserted += len(insert_values)
                    
                print(f"    -> [OSM] {clean_district} - {category}: +{len(insert_values)} items")
                time.sleep(1) # Tránh rate limit

            except Exception as e:
                print(f"    -> [OSM Error] {district_name} - {category}: {e}")
                db_session.rollback()

    print(f"--- [OSM] Hoàn tất. Tổng cộng: {total_inserted} địa điểm ---")