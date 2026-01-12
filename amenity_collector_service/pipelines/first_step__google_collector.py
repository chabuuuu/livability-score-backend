import os
import json
import time
import requests  # Thêm requests để gọi API mới
import pandas as pd
import geopandas as gpd
import numpy as np
import osmnx as ox
from shapely.geometry import Point, Polygon, MultiPolygon
from sqlalchemy import text
from dotenv import load_dotenv
from datetime import datetime, timezone
from shapely import wkt

# Import hàm lấy DB từ config mới
from config.property_db_config import get_property_db

load_dotenv()

# --- CẤU HÌNH GOOGLE MAPS ---
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Cấu hình Grid
CELL_SIZE_DEGREES = 0.01  # Kích thước ô lưới (~1.1km)
SEARCH_RADIUS_METERS = 750 # Bán kính tìm kiếm trong ô

API_CALL_LIMIT = int(os.getenv("MAP_FIRST_STEP_CALL_LIMIT", 50))

DISTRICT_NAMES = [
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

# Tham khảo: https://developers.google.com/maps/documentation/places/web-service/place-types
CATEGORY_TO_GOOGLE_TYPE = {
    'healthcare': ['hospital', 'pharmacy', 'doctor', 'chiropractor', 'dental_clinic', 'veterinary_care', 'dentist', 'drugstore', 'massage'],
    'education': ['school', 'university', 'primary_school', 'secondary_school', 'preschool', 'library'],
    'shopping': ['supermarket', 'shopping_mall', 'convenience_store', 'market', 'department_store', 'book_store', 'clothing_store', 'electronics_store', 'hardware_store', 'furniture_store', 'store'],
    'transportation': ['bus_station', 'train_station', 'subway_station', 'airport', 'taxi_stand', 'ferry_terminal'],
    'environment': ['park', 'tourist_attraction', 'zoo', 'aquarium', 'botanical_garden'],
    'entertainment': ['restaurant', 'cafe', 'bar', 'night_club', 'movie_theater', 'museum', 'art_gallery', 'amusement_park', 'stadium', 'performing_arts_theater'],
    'public_safety': ['police', 'fire_station', 'post_office', 'city_hall', 'courthouse']
}
CATEGORIES = list(CATEGORY_TO_GOOGLE_TYPE.keys())

# --- HELPER FUNCTIONS ---


def load_properties_from_db():
    """Load BĐS từ Database để xác định vùng cần quét."""
    print(f"--- [Google] Loading properties from Property Database...")
    
    db_gen = get_property_db()
    db = next(db_gen) 
    
    try:
        # Lấy tọa độ BĐS
        sql = """
            SELECT 
                ST_X(location::geometry) as longitude, 
                ST_Y(location::geometry) as latitude 
            FROM properties 
            WHERE location IS NOT NULL
        """
        df = pd.read_sql(sql, db.bind)
        
        if df.empty:
            print("⚠️ No properties found in database.")
            return None

        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df = df.dropna(subset=['longitude', 'latitude'])
        
        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
        
    except Exception as e:
        print(f"Error loading properties from DB: {e}")
        return None
    finally:
        db.close()

def get_district_boundaries(db_session):
    """Lấy ranh giới quận (Cache DB hoặc fetch OSM)."""
    print("--- [Google] Checking district boundaries cache...")
    try:
        sql_check = text("SELECT MAX(updated_at) FROM district_boundaries")
        last_update = db_session.execute(sql_check).scalar()
        
        is_stale = False
        if last_update:
            now = datetime.now(timezone.utc)
            if (now - last_update).days > 30: # Cache 30 ngày cho boundary
                is_stale = True
        else:
            is_stale = True

        if not is_stale:
            sql_load = text("SELECT district_name, ST_AsText(geometry) as geometry FROM district_boundaries")
            df = pd.read_sql(sql_load, db_session.bind)
            if not df.empty:
                df['geometry'] = df['geometry'].apply(wkt.loads)
                return gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

    except Exception as e:
        print(f"    -> DB Error checking cache: {e}")

    print("--- [Google] Fetching district boundaries from OSM (Refresh)...")
    gdfs = []
    districts_to_save = []

    for name in DISTRICT_NAMES:
        try:
            gdf = ox.geocode_to_gdf(name)
            short_name = name.split(',')[0]
            gdf['district_name'] = short_name
            
            geom = gdf.iloc[0].geometry
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon([geom])
            
            districts_to_save.append({
                "district_name": short_name,
                "geometry": geom.wkt
            })
            gdfs.append(gdf)
        except Exception:
            pass
    
    if not gdfs: return None
    
    # Save cache
    if districts_to_save:
        try:
            for dist in districts_to_save:
                sql_upsert = text("""
                    INSERT INTO district_boundaries (district_name, geometry, updated_at)
                    VALUES (:name, ST_GeomFromText(:geom, 4326), NOW())
                    ON CONFLICT (district_name) 
                    DO UPDATE SET geometry = EXCLUDED.geometry, updated_at = NOW();
                """)
                db_session.execute(sql_upsert, {"name": dist['district_name'], "geom": dist['geometry']})
            db_session.commit()
        except Exception as e:
            print(f"    -> Failed to save boundary cache: {e}")
            db_session.rollback()

    combined_gdf = pd.concat(gdfs, ignore_index=True)
    return gpd.GeoDataFrame(combined_gdf, crs="EPSG:4326")[['district_name', 'geometry']]

def create_grid(districts_gdf):
    """Tạo lưới phủ các quận."""
    total_bounds = districts_gdf.total_bounds
    xmin, ymin, xmax, ymax = total_bounds
    
    lons = np.arange(xmin, xmax, CELL_SIZE_DEGREES)
    lats = np.arange(ymin, ymax, CELL_SIZE_DEGREES)
    
    polygons = []
    for x in lons:
        for y in lats:
            polygons.append(Polygon([
                (x, y), (x + CELL_SIZE_DEGREES, y), 
                (x + CELL_SIZE_DEGREES, y + CELL_SIZE_DEGREES), (x, y + CELL_SIZE_DEGREES)
            ]))
            
    grid_gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326")
    grid_gdf['grid_center'] = grid_gdf.geometry.centroid
    
    # Chỉ lấy các ô lưới nằm trong các Quận
    grid_joined = gpd.sjoin(
        gpd.GeoDataFrame(grid_gdf, geometry='grid_center'), 
        districts_gdf, how="inner", predicate="intersects"
    )
    
    # Khôi phục geometry polygon
    grid_joined = grid_joined.set_geometry(grid_gdf.loc[grid_joined.index, 'geometry'])
    grid_joined.reset_index(drop=True, inplace=True)
    grid_joined['cell_id'] = grid_joined.index
    
    return grid_joined[['cell_id', 'geometry', 'district_name']]

def find_target_cells(grid_gdf, props_gdf):
    """
    Xác định các ô lưới cần quét.
    Logic: Chỉ quét các ô có chứa Bất động sản (Property Count > 0).
    Ưu tiên các ô có mật độ BĐS cao.
    """
    print("--- [Google] Identifying target cells based on Property Density...")
    
    # Đếm số lượng BĐS trong mỗi ô lưới
    joined_props = gpd.sjoin(props_gdf, grid_gdf, how="inner", predicate="within")
    prop_counts = joined_props.groupby('cell_id').size().reset_index(name='property_count')
    
    # Tạo danh sách task (Mỗi ô lưới x Mỗi category)
    # Vì Google Maps là nguồn duy nhất, ta quét đủ các category cho các ô có BĐS
    all_combinations = pd.MultiIndex.from_product(
        [grid_gdf['cell_id'], CATEGORIES], 
        names=['cell_id', 'category']
    ).to_frame(index=False)
    
    coverage = pd.merge(all_combinations, prop_counts, on='cell_id', how='left')
    coverage.fillna(0, inplace=True)
    
    # Lọc: Chỉ lấy ô có BĐS
    target_cells = coverage[coverage['property_count'] > 0].copy()
    
    # Sắp xếp: Ưu tiên ô nhiều BĐS nhất
    target_cells.sort_values(by='property_count', ascending=False, inplace=True)
    
    # Merge lại geometry để lấy tọa độ tâm
    target_cells = target_cells.merge(grid_gdf[['cell_id', 'geometry', 'district_name']], on='cell_id')
    
    return target_cells

def scan_google_maps(target_tasks, run_id, db_session, limit=API_CALL_LIMIT):
    """Quét Google Places API v1."""
    if not GOOGLE_API_KEY:
        print("--- [Google Scan] No API Key.")
        return 0

    api_calls = 0
    total_saved = 0
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.types,places.rating,places.location,places.formattedAddress,places.userRatingCount"
    }

    print(f"--- [Google Scan] Processing {len(target_tasks)} tasks with limit {limit}...")

    for idx, row in target_tasks.iterrows():
        if api_calls >= limit:
            print(f"--- [Google Scan] Reached limit ({limit}). Stopping.")
            break
            
        category = row['category']
        included_types = CATEGORY_TO_GOOGLE_TYPE.get(category, [])
        
        # Tọa độ tâm ô lưới
        center = row['geometry'].centroid
        lat, lng = center.y, center.x
        
        # print(f"    -> Querying '{category}' at Cell {row['cell_id']} ({row.get('district_name')})...")
        
        body = {
            "includedTypes": included_types,
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": SEARCH_RADIUS_METERS
                }
            },
            "languageCode": "vi"
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            api_calls += 1

            print('API CALL ' + str(api_calls))
            
            if response.status_code == 200:
                data = response.json()
                places = data.get('places', [])
                
                if places:
                    insert_values = []
                    for p in places:
                        place_id = p.get('id')
                        name = p.get('displayName', {}).get('text')
                        loc = p.get('location', {})
                        
                        if not name or not loc: continue
                        
                        # Chống trùng lặp ngay tại bước Insert vào bảng RAW trong cùng 1 Run
                        # (Mặc dù Syncer sẽ lọc lại, nhưng lọc sớm đỡ tốn DB)
                        
                        wkt_point = f"SRID=4326;POINT({loc['longitude']} {loc['latitude']})"
                        
                        insert_values.append({
                            "run_id": run_id,
                            "name": name,
                            "category": category,
                            "district": row.get('district_name', 'Unknown'),
                            "amenity_type": p.get('types', [])[0] if p.get('types') else 'unknown',
                            "longitude": loc['longitude'],
                            "latitude": loc['latitude'],
                            "google_place_id": place_id,
                            "google_rating": p.get('rating'),
                            "google_user_ratings_total": p.get('userRatingCount'),
                            "google_types": json.dumps(p.get('types', [])),
                            "vicinity": p.get('formattedAddress'),
                            "all_tags": json.dumps(p),
                            "location": wkt_point
                        })

                    if insert_values:
                        sql = text("""
                            INSERT INTO google_raw_amenities 
                            (run_id, name, category, district, amenity_type, longitude, latitude, 
                             google_place_id, google_rating, google_user_ratings_total, google_types, vicinity, all_tags, location)
                            VALUES (:run_id, :name, :category, :district, :amenity_type, :longitude, :latitude,
                                    :google_place_id, :google_rating, :google_user_ratings_total, :google_types, :vicinity, :all_tags, :location)
                        """)
                        db_session.execute(sql, insert_values)
                        db_session.commit()
                        total_saved += len(insert_values)

                        print('Insert ' + str(len(insert_values)) + ' rows for district ' + row.get('district_name', 'Unknown') + '. Total saved: ' + str(total_saved))
            
            time.sleep(0.5) # Delay nhẹ

        except Exception as e:
            print(f"    -> [Error] {e}")

    return total_saved

def run_google_pipeline(run_id, db_session):
    if not GOOGLE_API_KEY:
        print("Missing GOOGLE_MAPS_API_KEY")
        return

    print(f"=== START GOOGLE PIPELINE (Run ID: {run_id}) ===")
    
    # 1. Load BĐS
    props_gdf = load_properties_from_db()
    if props_gdf is None: return

    # 2. Load Boundary & Grid
    districts_gdf = get_district_boundaries(db_session)
    if districts_gdf is None: return
    grid_gdf = create_grid(districts_gdf)
    
    # 3. Tìm các ô lưới có BĐS (Target)
    target_tasks = find_target_cells(grid_gdf, props_gdf)
    print(f"--- Found {len(target_tasks)} tasks to scan.")
    
    # 4. Quét & Lưu DB
    total = scan_google_maps(target_tasks, run_id, db_session, limit=API_CALL_LIMIT)
    print(f"=== END GOOGLE PIPELINE. Saved {total} places. ===")