import os
import json
import time
import pandas as pd
import geopandas as gpd
import googlemaps
import numpy as np
import osmnx as ox
from shapely.geometry import Point, Polygon, MultiPolygon
from sqlalchemy import text
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from shapely import wkt

# Import hàm lấy DB từ config mới
from config.property_db_config import get_property_db

load_dotenv()

# --- CẤU HÌNH GOOGLE MAPS ---
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

# Cấu hình Grid
CELL_SIZE_DEGREES = 0.01  # Kích thước ô lưới (~1.1km)
SEARCH_RADIUS_METERS = 750 # Bán kính tìm kiếm trong ô

API_CALL_LIMIT = int(os.getenv("MAP_SECOND_STEP_CALL_LIMIT"))      # Giới hạn số request Google mỗi lần chạy

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

CATEGORY_TO_GOOGLE_TYPE = {
    'healthcare': 'hospital|pharmacy|doctor|clinic|dentist|nursing_home|veterinary_care',
    'education': 'school|university|primary_school|secondary_school|kindergarten|library|language_school',
    'shopping': 'supermarket|shopping_mall|convenience_store|market|department_store|book_store|clothing_store|electronics_store|hardware_store|furniture_store',
    'transportation': 'bus_station|train_station|subway_station|airport|taxi_stand|ferry_terminal',
    'environment': 'park|tourist_attraction|natural_feature|zoo|aquarium|botanical_garden',
    'entertainment': 'restaurant|cafe|bar|night_club|movie_theater|museum|art_gallery|amusement_park|stadium|performing_arts_theater',
    'public_safety': 'police|fire_station|post_office|city_hall|courthouse'
}
CATEGORIES = list(CATEGORY_TO_GOOGLE_TYPE.keys())

# --- HELPER FUNCTIONS ---

def load_properties_from_db():
    """Load BĐS từ Database Postgres để xác định mật độ tin đăng."""
    print(f"--- [Google] Loading properties from Property Database...")
    
    # Sử dụng generator get_property_db để lấy session
    db_gen = get_property_db()
    db = next(db_gen) # Lấy session từ generator
    
    try:
        # Query lấy trực tiếp tọa độ từ cột Geometry
        # Sử dụng db.bind làm engine kết nối cho pandas
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

        # Đảm bảo dữ liệu số
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df = df.dropna(subset=['longitude', 'latitude'])
        
        # Tạo GeoDataFrame
        geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
        return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
        
    except Exception as e:
        print(f"Error loading properties from DB: {e}")
        return None
    finally:
        db.close() # Đóng session sau khi dùng xong

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
    """
    Lấy ranh giới quận.
    - Ưu tiên lấy từ DB (bảng district_boundaries).
    - Nếu DB trống hoặc dữ liệu cũ > 7 ngày -> Gọi OSM API tải mới và lưu vào DB.
    """
    print("--- [Google] Checking district boundaries cache...")
    
    # 1. Kiểm tra dữ liệu trong DB
    try:
        # Lấy thời gian update mới nhất
        sql_check = text("SELECT MAX(updated_at) FROM district_boundaries")
        last_update = db_session.execute(sql_check).scalar()
        
        is_stale = False
        if last_update:
            # Nếu dùng timezone aware (Postgres timestamptz), cần convert now() cho khớp
            now = datetime.now(timezone.utc)
            if (now - last_update).days > 7:
                print(f"    -> Cache expired (Last update: {last_update}). Refreshing...")
                is_stale = True
            else:
                print(f"    -> Cache valid (Last update: {last_update}). Loading from DB.")
        else:
            print("    -> Cache empty. Fetching from OSM...")
            is_stale = True

        # 2. Nếu Cache hợp lệ -> Load từ DB
        if not is_stale:
            sql_load = text("SELECT district_name, ST_AsText(geometry) as geometry FROM district_boundaries")
            df = pd.read_sql(sql_load, db_session.bind)
            
            if not df.empty:
                # Convert WKT string thành Shapely Geometry
                df['geometry'] = df['geometry'].apply(wkt.loads)
                return gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

    except Exception as e:
        print(f"    -> DB Error checking cache: {e}. Fallback to OSM fetch.")

    # 3. Nếu Cache cũ hoặc trống -> Fetch từ OSM
    print("--- [Google] Fetching district boundaries from OSM (Network required)...")
    gdfs = []
    
    # Danh sách clean để insert
    districts_to_save = []

    for name in DISTRICT_NAMES:
        try:
            gdf = ox.geocode_to_gdf(name)
            # Lấy tên ngắn
            short_name = name.split(',')[0]
            gdf['district_name'] = short_name
            
            # Chuẩn bị geometry để lưu DB
            geom = gdf.iloc[0].geometry
            
            # PostGIS yêu cầu đúng định dạng (thường là MultiPolygon)
            # Nếu là Polygon đơn, convert sang MultiPolygon để đồng nhất
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon([geom])
            
            districts_to_save.append({
                "district_name": short_name,
                "geometry": geom.wkt # Convert sang WKT text để insert
            })
            
            gdfs.append(gdf)
            # time.sleep(1) # Nghỉ nhẹ để tránh OSM ban IP
            
        except Exception as e:
            print(f"    -> Failed to fetch {name}: {e}")
    
    if not gdfs:
        return None
    
    # Gộp GDF để trả về
    combined_gdf = pd.concat(gdfs, ignore_index=True)
    final_gdf = gpd.GeoDataFrame(combined_gdf, crs="EPSG:4326")[['district_name', 'geometry']]

    # 4. Lưu vào DB (Upsert)
    if districts_to_save:
        print(f"    -> Saving {len(districts_to_save)} districts to DB...")
        try:
            for dist in districts_to_save:
                # Sử dụng SQL thuần để Upsert (Insert on Conflict)
                sql_upsert = text("""
                    INSERT INTO district_boundaries (district_name, geometry, updated_at)
                    VALUES (:name, ST_GeomFromText(:geom, 4326), NOW())
                    ON CONFLICT (district_name) 
                    DO UPDATE SET 
                        geometry = EXCLUDED.geometry,
                        updated_at = NOW();
                """)
                db_session.execute(sql_upsert, {"name": dist['district_name'], "geom": dist['geometry']})
            
            db_session.commit()
            print("    -> Cache updated successfully.")
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
    
    # Gán quận cho từng ô lưới (Spatial Join)
    # Dùng centroid của ô lưới để check xem thuộc quận nào
    grid_gdf['grid_center'] = grid_gdf.geometry.centroid
    grid_joined = gpd.sjoin(
        gpd.GeoDataFrame(grid_gdf, geometry='grid_center'), 
        districts_gdf, 
        how="inner", 
        predicate="intersects" # Hoặc within
    )
    
    # Restore polygon geometry
    grid_joined = grid_joined.set_geometry(grid_gdf.loc[grid_joined.index, 'geometry'])
    grid_joined.reset_index(drop=True, inplace=True)
    grid_joined['cell_id'] = grid_joined.index
    
    return grid_joined[['cell_id', 'geometry', 'district_name']]

def find_sparse_cells(grid_gdf, osm_gdf, props_gdf):
    """Tìm các ô có BĐS nhưng thiếu OSM Amenities."""
    print("--- [Google] Identifying sparse cells (Gap Analysis)...")
    
    # 1. Đếm OSM trong từng ô theo Category
    joined_osm = gpd.sjoin(osm_gdf, grid_gdf, how="inner", predicate="within")
    osm_counts = joined_osm.groupby(['cell_id', 'category']).size().reset_index(name='osm_count')
    
    # 2. Đếm BĐS trong từng ô
    joined_props = gpd.sjoin(props_gdf, grid_gdf, how="inner", predicate="within")
    prop_counts = joined_props.groupby('cell_id').size().reset_index(name='property_count')
    
    # 3. Tạo bảng tổng hợp (Cell x Category)
    all_combinations = pd.MultiIndex.from_product(
        [grid_gdf['cell_id'], CATEGORIES], 
        names=['cell_id', 'category']
    ).to_frame(index=False)
    
    coverage = pd.merge(all_combinations, prop_counts, on='cell_id', how='left')
    coverage = pd.merge(coverage, osm_counts, on=['cell_id', 'category'], how='left')
    coverage.fillna(0, inplace=True)
    
    # 4. LỌC: Ô có BĐS > 0 (Ưu tiên nơi có người ở/bán)
    # Sắp xếp ưu tiên những nơi nhiều BĐS nhất
    target_cells = coverage[coverage['property_count'] > 0].copy()
    target_cells.sort_values(by='property_count', ascending=False, inplace=True)
    
    # Gắn lại thông tin hình học để lấy tâm ô lưới
    target_cells = target_cells.merge(grid_gdf[['cell_id', 'geometry', 'district_name']], on='cell_id')
    
    return target_cells

def scan_target_cells(target_tasks, run_id, db_session, limit=API_CALL_LIMIT):
    """
    Hàm thực hiện quét Google Maps dựa trên danh sách các ô (tasks) được giao.
    Có thể dùng cho Pipeline chính hoặc Targeted Pipeline.
    """
    if not gmaps:
        print("--- [Google Scan] No API Key.")
        return 0

    api_calls = 0
    total_saved = 0
    
    print(f"--- [Google Scan] Processing {len(target_tasks)} tasks...")

    for idx, row in target_tasks.iterrows():
        if api_calls >= limit:
            print(f"--- [Google Scan] Reached limit ({limit}). Stopping.")
            break
            
        category = row['category']
        keywords = CATEGORY_TO_GOOGLE_TYPE.get(category, "")
        
        center = row['geometry'].centroid
        lat, lng = center.y, center.x
        
        print(f"    -> [Call {api_calls+1}] Querying '{category}' at Cell {row['cell_id']} ({row.get('district_name', 'Unknown')})...")
        
        try:
            places_result = gmaps.places_nearby(
                location=(lat, lng),
                radius=SEARCH_RADIUS_METERS,
                keyword=keywords.replace("|", " OR "),
                type=keywords.split('|')[0],
                language='vi'
            )
            api_calls += 1
            
            results = places_result.get('results', [])
            if not results:
                time.sleep(1)
                continue

            insert_values = []
            for p in results:
                ploc = p['geometry']['location']
                wkt_point = f"SRID=4326;POINT({ploc['lng']} {ploc['lat']})"
                
                if 'name' not in p: continue

                # Logic chống trùng ngay tại bảng RAW:
                # Nếu google_place_id đã có trong run_id này thì không insert nữa
                # (Lưu ý: Logic này chỉ check trong memory của batch hiện tại hoặc cần query DB check tồn tại)
                # Để đơn giản và nhanh, ta cứ insert, sau này Syncer sẽ lo việc distinct google_place_id
                
                insert_values.append({
                    "run_id": run_id,
                    "name": p.get('name'),
                    "category": category,
                    "district": row.get('district_name', 'Unknown'),
                    "amenity_type": p.get('types', [])[0] if p.get('types') else 'unknown',
                    "longitude": ploc['lng'],
                    "latitude": ploc['lat'],
                    "google_place_id": p.get('place_id'),
                    "google_rating": p.get('rating'),
                    "google_types": json.dumps(p.get('types', [])),
                    "vicinity": p.get('vicinity'),
                    "all_tags": json.dumps(p),
                    "location": wkt_point
                })

            if insert_values:
                # Sử dụng ON CONFLICT DO NOTHING để chống trùng lặp trong cùng 1 RUN nếu lỡ quét lại vùng đó
                # Yêu cầu bảng google_raw_amenities cần có UNIQUE CONSTRAINT (run_id, google_place_id) nếu muốn chặt chẽ
                # Hoặc chỉ đơn giản insert, syncer xử lý sau.
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
            
            time.sleep(2)

        except Exception as e:
            print(f"    -> [Google Error]: {e}")

    return total_saved

# --- MAIN PIPELINE FUNCTION ---
def run_google_pipeline(run_id, db_session):
    if not gmaps: return

    print(f"--- [Google Pipeline] Start Gap Analysis for Run ID: {run_id} ---")
    
    # 1. Load Data (Properties & OSM Raw)
    props_gdf = load_properties_from_db()
    if props_gdf is None: return
    
    osm_gdf = load_osm_gdf_from_db(run_id, db_session)
    if osm_gdf is None: osm_gdf = gpd.GeoDataFrame(columns=['category', 'geometry'], crs="EPSG:4326")

    # 2. Grid & Analysis
    districts_gdf = get_district_boundaries(db_session)
    if districts_gdf is None: return
    grid_gdf = create_grid(districts_gdf)
    
    # Tìm các ô thưa thớt
    target_tasks = find_sparse_cells(grid_gdf, osm_gdf, props_gdf)
    print(f"--- [Google Pipeline] Found {len(target_tasks)} sparse cells.")
    
    # 3. Scan
    total = scan_target_cells(target_tasks, run_id, db_session, limit=API_CALL_LIMIT)
    print(f"--- [Google Pipeline] Done. Saved {total} places. ---")