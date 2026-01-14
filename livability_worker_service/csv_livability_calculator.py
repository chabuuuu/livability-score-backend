import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
from shapely import wkt
import time
import os

# --- CẤU HÌNH THAM SỐ (HYBRID MODEL) ---
CONSTANTS = {
    # Nhóm Thiết yếu (Ưu tiên Khoảng cách - Alpha cao)
    'healthcare': {
        'max_dist': 1500, 'radius': 1500, 'max_count': 5, 'alpha': 0.7
    },
    'education': {
        'max_dist': 1000, 'radius': 1000, 'max_count': 5, 'alpha': 0.6
    },
    'public_safety': {
        'max_dist': 1000, 'radius': 1000, 'max_count': 3, 'alpha': 0.7
    },
    'transportation': {
        'max_dist': 500,  'radius': 800,  'max_count': 5, 'alpha': 0.6
    },
    'environment': {
        'max_dist': 1000, 'radius': 1000, 'max_count': 3, 'alpha': 0.5
    },
    
    # Nhóm Lựa chọn/Tụ tập (Ưu tiên Mật độ - Alpha thấp)
    'shopping': {
        'max_dist': 1000, 'radius': 500,  'max_count': 15, 'alpha': 0.3
    },
    'entertainment': {
        'max_dist': 1000, 'radius': 1000, 'max_count': 20, 'alpha': 0.3
    }
}

# Mapping tên category từ CSV amenities sang key trong CONSTANTS
# Nếu CSV của bạn dùng tên khác (ví dụ 'park' thay vì 'environment'), hãy sửa mapping ở đây
# Dựa trên file amenities.csv bạn cung cấp, category có vẻ đã chuẩn.
CATEGORY_MAPPING = {
    'healthcare': 'healthcare',
    'education': 'education',
    'public_safety': 'public_safety', # Có thể cần map 'police', 'fire_station' về đây nếu csv chưa chuẩn
    'transportation': 'transportation',
    'environment': 'environment',
    'shopping': 'shopping',
    'entertainment': 'entertainment'
}

# --- HÀM HỖ TRỢ ---
def haversine_vectorized(lat1, lon1, lat2, lon2):
    """Tính khoảng cách (mét) giữa 2 bộ tọa độ dùng công thức Haversine (Vector hóa)"""
    R = 6371000  # Bán kính trái đất (mét)
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

def normalize_score(value, max_val, mode='distance'):
    """Chuẩn hóa điểm về 0-100"""
    if mode == 'distance':
        if pd.isna(value) or value == float('inf') or value > max_val: 
            return 0.0
        return 100.0 * (1 - value / max_val)
    elif mode == 'count':
        if pd.isna(value): return 0.0
        return 100.0 * min(1, value / max_val)
    return 0.0

def parse_wkt_point(wkt_str):
    """Parse 'POINT (lng lat)' thành (lat, lng)"""
    try:
        pt = wkt.loads(wkt_str)
        return pt.y, pt.x # Lat, Lng
    except:
        return np.nan, np.nan

# --- CLASS XỬ LÝ CHÍNH ---
class CsvLivabilityProcessor:
    def __init__(self, amenities_file):
        print("⏳ Đang tải và đánh chỉ mục Amenities...")
        self.amenities_df = pd.read_csv(amenities_file)
        
        # Xây dựng KDTree cho từng loại Category để tìm kiếm nhanh
        self.trees = {}
        self.amenity_data = {}

        # Tiền xử lý tọa độ Amenities
        # KDTree làm việc trên không gian Euclid, ta dùng xấp xỉ Lat/Lng -> Descartes
        # Tuy nhiên để chính xác khoảng cách mét, ta sẽ dùng Tree để lọc ứng viên gần nhất (bán kính thô)
        # sau đó tính Haversine chính xác.
        
        # Nhóm amenities theo category
        grouped = self.amenities_df.groupby('category')
        
        for cat, group in grouped:
            # Map category trong CSV sang key cấu hình (nếu cần)
            config_key = cat # Giả sử tên khớp nhau
            if config_key not in CONSTANTS:
                continue
                
            coords = group[['latitude', 'longitude']].values
            self.trees[config_key] = cKDTree(coords)
            self.amenity_data[config_key] = coords

        print("✅ Đã xây dựng Spatial Index cho Amenities.")

    def process_properties(self, input_file, output_file, batch_size=1000):
        print(f"🚀 Bắt đầu xử lý file: {input_file}")
        
        # Đọc file CSV theo từng chunk
        chunk_iter = pd.read_csv(input_file, chunksize=batch_size)
        
        first_chunk = True
        total_processed = 0
        start_time = time.time()

        for chunk in chunk_iter:
            # --- 1. XỬ LÝ TỌA ĐỘ (SỬA LỖI Ở ĐÂY) ---
            # Logic: Ưu tiên dùng location (WKT) nếu cột latitude/longitude không tồn tại hoặc bị rỗng
            
            has_lat_col = 'latitude' in chunk.columns
            has_lng_col = 'longitude' in chunk.columns
            has_location_col = 'location' in chunk.columns

            # Trường hợp 1: Có cột location, và (không có cột lat/lng HOẶC cột lat/lng bị rỗng) -> Parse WKT
            if has_location_col and (not has_lat_col or not has_lng_col or chunk['latitude'].isnull().all()):
                # Parse WKT thành tuple (lat, lng)
                # zip(*...) giúp tách list các tuple thành 2 list riêng biệt
                try:
                    chunk['latitude'], chunk['longitude'] = zip(*chunk['location'].apply(parse_wkt_point))
                except Exception as e:
                    print(f"⚠️ Lỗi parse WKT trong chunk hiện tại: {e}")
                    continue
            
            # Trường hợp 2: Không có location, nhưng cũng không có lat/lng -> Bỏ qua chunk này
            elif not has_lat_col or not has_lng_col:
                # Nếu không parse được từ location và cũng không có sẵn cột lat/lng
                print("⚠️ Chunk thiếu dữ liệu tọa độ. Bỏ qua.")
                continue

            # --- Kết thúc xử lý tọa độ ---

            # Lọc bỏ các dòng mà tọa độ vẫn là NaN sau khi xử lý
            valid_props = chunk.dropna(subset=['latitude', 'longitude'])
            
            if valid_props.empty:
                continue

            # Lấy mảng tọa độ để tính toán (dùng cột latitude, longitude chuẩn)
            prop_coords = valid_props[['latitude', 'longitude']].values

            # 2. Tính toán Score cho từng Category
            for cat_key, config in CONSTANTS.items():
                if cat_key not in self.trees:
                    chunk[f'dist_{cat_key}'] = np.nan
                    chunk[f'count_{cat_key}'] = 0
                    chunk[f'score_{cat_key}'] = 0
                    continue

                tree = self.trees[cat_key]
                am_coords = self.amenity_data[cat_key]
                
                # --- A. TÍNH KHOẢNG CÁCH GẦN NHẤT (MIN DISTANCE) ---
                _, idxs = tree.query(prop_coords, k=1)
                nearest_am_coords = am_coords[idxs]
                
                # Tính khoảng cách thực tế (mét)
                dists_meters = haversine_vectorized(
                    prop_coords[:, 0], prop_coords[:, 1],
                    nearest_am_coords[:, 0], nearest_am_coords[:, 1]
                )
                
                chunk.loc[valid_props.index, f'dist_{cat_key}'] = dists_meters

                # --- B. TÍNH MẬT ĐỘ (COUNT) ---
                radius_deg = config['radius'] / 110000.0 
                counts = [len(c) for c in tree.query_ball_point(prop_coords, r=radius_deg)]
                chunk.loc[valid_props.index, f'count_{cat_key}'] = counts

                # --- C. TÍNH SCORE HYBRID ---
                d_col = chunk.loc[valid_props.index, f'dist_{cat_key}']
                c_col = chunk.loc[valid_props.index, f'count_{cat_key}']
                
                s_dist = np.where(d_col > config['max_dist'], 0, 100 * (1 - d_col / config['max_dist']))
                s_dist = np.maximum(s_dist, 0)
                
                s_count = 100 * (c_col / config['max_count'])
                s_count = np.minimum(s_count, 100)
                
                alpha = config['alpha']
                final_score = (alpha * s_dist) + ((1 - alpha) * s_count)
                
                chunk.loc[valid_props.index, f'score_{cat_key}'] = final_score

            # 3. Ghi ra file CSV
            mode = 'w' if first_chunk else 'a'
            header = first_chunk
            
            # Danh sách cột output mong muốn
            required_cols = [
                'id','title','description','listing_type','price','price_unit','area',
                'property_type','legal_status','num_bedrooms','num_bathrooms','num_floors',
                'facade_width_m','road_width_m','house_direction','balcony_direction',
                'furniture_status','project_name','building_block','floor_number',
                'address_street','address_ward','address_district','address_city','location',
                'features','source_url','source_listing_id','posted_at','created_at','updated_at',
                'provider','longitude','latitude' 
            ]
            
            # Thêm các cột metric mới
            score_cols = []
            for key in CONSTANTS.keys():
                score_cols.extend([f'dist_{key}', f'count_{key}', f'score_{key}'])
                
            # Tạo các cột còn thiếu trong chunk (nếu có) để không bị lỗi khi ghi file
            for col in required_cols:
                if col not in chunk.columns:
                    chunk[col] = np.nan
                    
            # Map tên cột (Rename)
            rename_map = {
                'dist_public_safety': 'dist_safety',
                'count_public_safety': 'count_safety',
                'score_public_safety': 'score_safety',
                'dist_transportation': 'dist_transport',
                'count_transportation': 'count_transport',
                'score_transportation': 'score_transportation'
            }
            chunk = chunk.rename(columns=rename_map)
            
            # Chuẩn bị list cột cuối cùng
            final_score_cols = [rename_map.get(col, col) for col in score_cols]
            final_output_cols = required_cols + final_score_cols
            
            # Chỉ ghi những cột thực sự tồn tại trong DataFrame
            valid_output_cols = [c for c in final_output_cols if c in chunk.columns]
            
            chunk.to_csv(output_file, mode=mode, header=header, index=False, columns=valid_output_cols)
            
            first_chunk = False
            total_processed += len(chunk)
            print(f"📦 Đã xử lý: {total_processed} căn...")

        duration = time.time() - start_time
        print(f"\n✅ HOÀN THÀNH! Tổng thời gian: {duration:.2f} giây.")
        print(f"📁 Kết quả lưu tại: {output_file}")

# --- CHẠY CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    INPUT_PROPS = 'properties.csv'
    INPUT_AMENITIES = 'amenities.csv'
    OUTPUT_FILE = 'properties_scored_hybrid.csv'
    
    if not os.path.exists(INPUT_PROPS) or not os.path.exists(INPUT_AMENITIES):
        print("❌ Lỗi: Không tìm thấy file csv đầu vào.")
    else:
        processor = CsvLivabilityProcessor(INPUT_AMENITIES)
        processor.process_properties(INPUT_PROPS, OUTPUT_FILE)