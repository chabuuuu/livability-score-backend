import os
import json
import time
import pandas as pd
import geopandas as gpd
import googlemaps
import numpy as np
import osmnx as ox
from shapely.geometry import Point, Polygon
from sqlalchemy import text
from dotenv import load_dotenv

# Import hàm lấy DB từ config mới
from config.property_db_config import get_property_db

load_dotenv()

# --- CẤU HÌNH GOOGLE MAPS ---
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

# Cấu hình Grid
CELL_SIZE_DEGREES = 0.01  # Kích thước ô lưới (~1.1km)
SEARCH_RADIUS_METERS = 750 # Bán kính tìm kiếm trong ô
API_CALL_LIMIT = 2500      # Giới hạn số request Google mỗi lần chạy

DISTRICT_NAMES = [
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

CATEGORY_TO_GOOGLE_TYPE = {
    # 🏥 Sức khỏe & Y tế
    # 'hospital', 'pharmacy', 'doctor', 'clinic', 'dentist' là các loại (type) chính thức.
    'healthcare': 'hospital|pharmacy|doctor|clinic|dentist|nursing_home|veterinary_care',

    # 🎓 Giáo dục
    # 'school', 'university' là loại chính. Thêm 'primary_school', 'secondary_school', 'kindergarten' 
    # làm từ khóa để bắt các trường hợp OSM có thể đã bỏ lỡ.
    'education': 'school|university|primary_school|secondary_school|kindergarten|library|language_school',

    # 🛍️ Mua sắm
    # 'supermarket', 'convenience_store', 'shopping_mall', 'department_store' là các loại chính.
    # 'market' (chợ) cũng là một loại.
    'shopping': 'supermarket|shopping_mall|convenience_store|market|department_store|book_store|clothing_store|electronics_store|hardware_store|furniture_store',

    # 🚌 Giao thông
    # 'bus_station', 'train_station', 'subway_station', 'airport', 'light_rail_station' là các loại chính.
    'transportation': 'bus_station|train_station|subway_station|airport|taxi_stand|ferry_terminal',

    # 🌳 Môi trường & Không gian xanh
    # 'park' là loại chính. 'natural_feature' có thể bao gồm sông, núi. 'tourist_attraction' thường bao gồm các công viên lớn.
    'environment': 'park|tourist_attraction|natural_feature|zoo|aquarium|botanical_garden',

    # 🎭 Văn hóa & Giải trí
    # 'restaurant', 'cafe', 'bar', 'movie_theater', 'museum', 'art_gallery' là các loại chính.
    'entertainment': 'restaurant|cafe|bar|night_club|movie_theater|museum|art_gallery|amusement_park|stadium|performing_arts_theater',

    # 🏛️ Dịch vụ công & An ninh
    # 'police', 'fire_station', 'post_office' là các loại chính.
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

def get_district_boundaries():
    print("--- [Google] Fetching district boundaries from OSM (Network required)...")
    gdfs = []
    for name in DISTRICT_NAMES:
        try:
            gdf = ox.geocode_to_gdf(name)
            gdf['district_name'] = name.split(',')[0]
            gdfs.append(gdf)
        except Exception:
            pass # Bỏ qua nếu lỗi mạng hoặc không tìm thấy
    
    if not gdfs:
        return None
    
    # Gộp và chỉ giữ lại cột cần thiết
    combined = pd.concat(gdfs, ignore_index=True)
    return gpd.GeoDataFrame(combined, crs="EPSG:4326")[['district_name', 'geometry']]

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

# --- MAIN PIPELINE FUNCTION ---

def run_google_pipeline(run_id, db_session):
    if not gmaps:
        print("--- [Google] No API Key. Skipping Google Pipeline.")
        return

    print(f"--- [Google] Starting Pipeline for Run ID: {run_id} ---")
    
    # 1. Load Data
    # Thay đổi: Gọi hàm load từ DB thay vì file
    props_gdf = load_properties_from_db()
    if props_gdf is None:
        return

    osm_gdf = load_osm_gdf_from_db(run_id, db_session)
    # Lưu ý: osm_gdf có thể None nếu bước 1 OSM failed, vẫn chạy tiếp để Google cứu cánh
    if osm_gdf is None:
        osm_gdf = gpd.GeoDataFrame(columns=['category', 'geometry'], crs="EPSG:4326")

    # 2. Prepare Grid
    districts_gdf = get_district_boundaries()
    if districts_gdf is None:
        print("--- [Google] Could not load district boundaries from OSM. Aborting.")
        return
        
    grid_gdf = create_grid(districts_gdf)
    
    # 3. Gap Analysis
    target_tasks = find_sparse_cells(grid_gdf, osm_gdf, props_gdf)
    print(f"--- [Google] Identified {len(target_tasks)} tasks (Cells * Categories) for scanning.")
    
    # 4. Fetch & Save
    api_calls = 0
    total_saved = 0
    
    # Duyệt qua danh sách task
    for idx, row in target_tasks.iterrows():
        if api_calls >= API_CALL_LIMIT:
            print(f"--- [Google] Reached API limit ({API_CALL_LIMIT}). Stopping.")
            break
            
        category = row['category']
        keywords = CATEGORY_TO_GOOGLE_TYPE.get(category, "")
        
        # Lấy tâm ô lưới để scan
        center = row['geometry'].centroid
        lat, lng = center.y, center.x
        
        print(f"    -> [Call {api_calls+1}] Querying '{category}' at Cell {row['cell_id']} ({row['district_name']})...")
        
        try:
            # Gọi Google Maps API
            # Lưu ý: keyword hỗ trợ logic OR bằng dấu '|' không chính thức trong python client,
            # nhưng ta truyền chuỗi vào hy vọng client handle hoặc API hiểu.
            # Tốt nhất dùng keyword parameter.
            places_result = gmaps.places_nearby(
                location=(lat, lng),
                radius=SEARCH_RADIUS_METERS,
                keyword=keywords.replace("|", " OR "), # Thử dùng OR cho keyword search
                type=keywords.split('|')[0], # Fallback type chính
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
                
                # Check data integrity
                if 'name' not in p: continue

                insert_values.append({
                    "run_id": run_id,
                    "name": p.get('name'),
                    "category": category,
                    "district": row['district_name'],
                    "amenity_type": p.get('types', [])[0] if p.get('types') else 'unknown',
                    "longitude": ploc['lng'],
                    "latitude": ploc['lat'],
                    "google_place_id": p.get('place_id'),
                    "google_rating": p.get('rating'),
                    "google_types": json.dumps(p.get('types', [])),
                    "vicinity": p.get('vicinity'),
                    "all_tags": json.dumps(p), # Lưu full response làm raw
                    "location": wkt_point
                })

            if insert_values:
                # Insert vào DB (google_raw_amenities)
                # Ta insert hết, việc chống trùng lặp (nếu có trùng trong cùng 1 lần quét) sẽ do Syncer lo
                # Hoặc bảng raw có thể chấp nhận trùng.
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
            
            time.sleep(2) # Rate limit safety

        except Exception as e:
            print(f"    -> [Google Error]: {e}")
            # db_session.rollback() # Rollback nếu cần, nhưng ở đây ta commit từng batch

    print(f"--- [Google] Completed. Total saved: {total_saved} places. API Calls: {api_calls}. ---")