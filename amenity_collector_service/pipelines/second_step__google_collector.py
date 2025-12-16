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

API_CALL_LIMIT = int(os.getenv("MAP_SECOND_STEP_CALL_LIMIT", 50))

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

# Cập nhật danh sách loại địa điểm theo chuẩn Places API (New)
# Tham khảo: https://developers.google.com/maps/documentation/places/web-service/place-types
CATEGORY_TO_GOOGLE_TYPE = {
    'healthcare': ['hospital', 'pharmacy', 'doctor', 'medical_clinic', 'dental_clinic', 'veterinary_care'],
    'education': ['school', 'university', 'primary_school', 'secondary_school', 'preschool', 'library'],
    'shopping': ['supermarket', 'shopping_mall', 'convenience_store', 'market', 'department_store', 'book_store', 'clothing_store', 'electronics_store', 'hardware_store', 'furniture_store'],
    'transportation': ['bus_station', 'train_station', 'subway_station', 'airport', 'taxi_stand', 'ferry_terminal'],
    'environment': ['park', 'tourist_attraction', 'zoo', 'aquarium', 'botanical_garden'],
    'entertainment': ['restaurant', 'cafe', 'bar', 'night_club', 'movie_theater', 'museum', 'art_gallery', 'amusement_park', 'stadium', 'performing_arts_theater'],
    'public_safety': ['police', 'fire_station', 'post_office', 'city_hall', 'courthouse']
}
CATEGORIES = list(CATEGORY_TO_GOOGLE_TYPE.keys())

# --- HELPER FUNCTIONS ---

def load_properties_from_db():
    """Load BĐS từ Database Postgres để xác định mật độ tin đăng."""
    print(f"--- [Google] Loading properties from Property Database...")
    
    db_gen = get_property_db()
    db = next(db_gen) 
    
    try:
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

def load_osm_gdf_from_db(run_id, db_session):
    """Load dữ liệu OSM vừa thu thập (trong cùng run_id) từ DB."""
    print(f"--- [Google] Loading OSM data for Run ID {run_id} from DB...")
    sql = text("SELECT category, longitude, latitude FROM osm_raw_amenities WHERE run_id = :run_id")
    try:
        df = pd.read_sql(sql, db_session.bind, params={"run_id": run_id})
        if df.empty:
            print("--- [Google] OSM data is empty. Will scan strictly based on properties.")
            return gpd.GeoDataFrame(columns=['category', 'geometry'], crs="EPSG:4326")
        
        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    except Exception as e:
        print(f"Error loading OSM from DB: {e}")
        return None

def get_district_boundaries(db_session):
    """Lấy ranh giới quận (Ưu tiên DB, Fallback OSM)."""
    print("--- [Google] Checking district boundaries cache...")
    try:
        sql_check = text("SELECT MAX(updated_at) FROM district_boundaries")
        last_update = db_session.execute(sql_check).scalar()
        
        is_stale = False
        if last_update:
            now = datetime.now(timezone.utc)
            if (now - last_update).days > 7:
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
        print(f"    -> DB Error checking cache: {e}. Fallback to OSM fetch.")

    print("--- [Google] Fetching district boundaries from OSM (Network required)...")
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
        except Exception as e:
            print(f"    -> Failed to fetch {name}: {e}")
    
    if not gdfs: return None
    
    combined_gdf = pd.concat(gdfs, ignore_index=True)
    final_gdf = gpd.GeoDataFrame(combined_gdf, crs="EPSG:4326")[['district_name', 'geometry']]

    if districts_to_save:
        print(f"    -> Saving {len(districts_to_save)} districts to DB...")
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
            print(f"    -> Failed to save cache: {e}")
            db_session.rollback()

    return final_gdf

def create_grid(districts_gdf):
    """Tạo lưới bao phủ các quận."""
    print("--- [Google] Creating analysis grid...")
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
    grid_joined = gpd.sjoin(
        gpd.GeoDataFrame(grid_gdf, geometry='grid_center'), 
        districts_gdf, how="inner", predicate="intersects"
    )
    
    grid_joined = grid_joined.set_geometry(grid_gdf.loc[grid_joined.index, 'geometry'])
    grid_joined.reset_index(drop=True, inplace=True)
    grid_joined['cell_id'] = grid_joined.index
    
    return grid_joined[['cell_id', 'geometry', 'district_name']]

def find_sparse_cells(grid_gdf, osm_gdf, props_gdf):
    """Tìm các ô có BĐS nhưng thiếu OSM Amenities."""
    print("--- [Google] Identifying sparse cells (Gap Analysis)...")
    
    joined_osm = gpd.sjoin(osm_gdf, grid_gdf, how="inner", predicate="within")
    osm_counts = joined_osm.groupby(['cell_id', 'category']).size().reset_index(name='osm_count')
    
    joined_props = gpd.sjoin(props_gdf, grid_gdf, how="inner", predicate="within")
    prop_counts = joined_props.groupby('cell_id').size().reset_index(name='property_count')
    
    all_combinations = pd.MultiIndex.from_product(
        [grid_gdf['cell_id'], CATEGORIES], 
        names=['cell_id', 'category']
    ).to_frame(index=False)
    
    coverage = pd.merge(all_combinations, prop_counts, on='cell_id', how='left')
    coverage = pd.merge(coverage, osm_counts, on=['cell_id', 'category'], how='left')
    coverage.fillna(0, inplace=True)
    
    target_cells = coverage[coverage['property_count'] > 0].copy()
    target_cells.sort_values(by='property_count', ascending=False, inplace=True)
    target_cells = target_cells.merge(grid_gdf[['cell_id', 'geometry', 'district_name']], on='cell_id')
    
    return target_cells

def scan_target_cells(target_tasks, run_id, db_session, limit=API_CALL_LIMIT):
    """
    Hàm thực hiện quét Google Places API (New) (v1).
    Sử dụng 'places:searchNearby' với POST request.
    """
    if not GOOGLE_API_KEY:
        print("--- [Google Scan] No API Key.")
        return 0

    api_calls = 0
    total_saved = 0
    
    # Endpoint cho API mới
    url = "https://places.googleapis.com/v1/places:searchNearby"
    
    # Headers bắt buộc cho API mới
    # FieldMask giúp tối ưu chi phí, chỉ lấy trường cần thiết
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.types,places.rating,places.location,places.formattedAddress"
    }

    print(f"--- [Google Scan] Processing {len(target_tasks)} tasks...")

    for idx, row in target_tasks.iterrows():
        if api_calls >= limit:
            print(f"--- [Google Scan] Reached limit ({limit}). Stopping.")
            break
            
        category = row['category']
        included_types = CATEGORY_TO_GOOGLE_TYPE.get(category, [])
        
        if not included_types:
            continue
        
        center = row['geometry'].centroid
        lat, lng = center.y, center.x
        
        print(f"    -> [Call {api_calls+1}] Querying '{category}' at Cell {row['cell_id']} ({row.get('district_name', 'Unknown')})...")
        
        # Body cho Request
        body = {
            "includedTypes": included_types,
            "maxResultCount": 20, # Max là 20 cho 1 trang
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng
                    },
                    "radius": SEARCH_RADIUS_METERS
                }
            },
            "languageCode": "vi"
        }

        try:
            response = requests.post(url, headers=headers, json=body)
            api_calls += 1
            
            if response.status_code != 200:
                print(f"    -> [Google Error] Status {response.status_code}: {response.text}")
                continue

            data = response.json()
            places_result = data.get('places', [])
            
            if not places_result:
                time.sleep(1)
                continue

            insert_values = []
            for p in places_result:
                # Xử lý các trường từ response mới
                # id -> google_place_id
                # displayName.text -> name
                # location -> longitude/latitude
                # formattedAddress -> vicinity (tạm dùng thay thế)
                
                place_id = p.get('id')
                name = p.get('displayName', {}).get('text')
                loc = p.get('location', {})
                pl_lat = loc.get('latitude')
                pl_lng = loc.get('longitude')
                
                if not name or not pl_lat or not pl_lng: continue

                wkt_point = f"SRID=4326;POINT({pl_lng} {pl_lat})"
                
                insert_values.append({
                    "run_id": run_id,
                    "name": name,
                    "category": category,
                    "district": row.get('district_name', 'Unknown'),
                    "amenity_type": p.get('types', [])[0] if p.get('types') else 'unknown',
                    "longitude": pl_lng,
                    "latitude": pl_lat,
                    "google_place_id": place_id,
                    "google_rating": p.get('rating'),
                    "google_types": json.dumps(p.get('types', [])),
                    "vicinity": p.get('formattedAddress'),
                    "all_tags": json.dumps(p),
                    "location": wkt_point
                })

            if insert_values:
                # Lưu vào DB
                sql = text("""
                    INSERT INTO google_raw_amenities 
                    (run_id, name, category, district, amenity_type, longitude, latitude, 
                     google_place_id, google_rating, google_types, vicinity, all_tags, location)
                    VALUES (:run_id, :name, :category, :district, :amenity_type, :longitude, :latitude,
                            :google_place_id, :google_rating, :google_types, :vicinity, :all_tags, :location)
                """)
                db_session.execute(sql, insert_values)
                db_session.commit()
                total_saved += len(insert_values)
            
            time.sleep(2) # Rate limit an toàn

        except Exception as e:
            print(f"    -> [Exception]: {e}")

    return total_saved

# --- MAIN PIPELINE FUNCTION ---
def run_google_pipeline(run_id, db_session):
    if not GOOGLE_API_KEY: 
        print("Missing GOOGLE_MAPS_API_KEY")
        return

    print(f"--- [Google Pipeline] Start Gap Analysis for Run ID: {run_id} ---")
    
    # 1. Load Data
    props_gdf = load_properties_from_db()
    if props_gdf is None: return
    
    osm_gdf = load_osm_gdf_from_db(run_id, db_session)
    if osm_gdf is None: osm_gdf = gpd.GeoDataFrame(columns=['category', 'geometry'], crs="EPSG:4326")

    # 2. Grid & Analysis
    districts_gdf = get_district_boundaries(db_session)
    if districts_gdf is None: return
    grid_gdf = create_grid(districts_gdf)
    
    target_tasks = find_sparse_cells(grid_gdf, osm_gdf, props_gdf)
    print(f"--- [Google Pipeline] Found {len(target_tasks)} sparse cells.")
    
    # 3. Scan with New API
    total = scan_target_cells(target_tasks, run_id, db_session, limit=API_CALL_LIMIT)
    print(f"--- [Google Pipeline] Done. Saved {total} places. ---")