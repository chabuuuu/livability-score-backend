from sqlalchemy.orm import Session
from sqlalchemy import text

from model.PropertyLivabilityScore import PropertyLivabilityScore

# --- CẤU HÌNH THAM SỐ (Giống code cũ của bạn) ---
CONSTANTS = {
    'healthcare': {'max_dist': 1500, 'type': 'distance'},
    'education': {'max_dist': 1000, 'type': 'distance'},
    'transportation': {'max_dist': 500, 'type': 'distance'},
    'environment': {'max_dist': 1000, 'type': 'distance'}, # Công viên/Cây xanh
    'public_safety': {'max_dist': 1000, 'type': 'distance'},
    
    'shopping': {'radius': 500, 'max_count': 15, 'type': 'count'},
    'entertainment': {'radius': 1000, 'max_count': 20, 'type': 'count'}
}

# Mapping Category trong bảng amenities với key tính toán
CATEGORY_MAPPING = {
    'healthcare': ['hospital', 'clinic', 'pharmacy', 'healthcare'],
    'education': ['school', 'university', 'college', 'kindergarten', 'education'],
    'transportation': ['bus_station', 'subway_station', 'transit_station', 'transportation'],
    'environment': ['park', 'garden', 'nature_reserve', 'environment'],
    'public_safety': ['police', 'fire_station', 'public_safety'],
    'shopping': ['supermarket', 'mall', 'market', 'convenience_store', 'shopping'],
    'entertainment': ['cinema', 'theater', 'bar', 'club', 'cafe', 'entertainment']
}

class LivabilityCalculator:
    # Cập nhật init để nhận 2 session riêng biệt
    def __init__(self, db_prop: Session, scoring_db: Session):
        self.db_prop = db_prop
        self.scoring_db = scoring_db

    def normalize_score(self, value, max_val, mode='distance'):
        """Chuẩn hóa điểm về 0-100"""
        if mode == 'distance':
            # Khoảng cách càng nhỏ càng tốt
            if value is None or value == float('inf'): return 0
            score = 100 * (1 - min(value, max_val) / max_val)
            return max(0, score)
        elif mode == 'count':
            # Số lượng càng nhiều càng tốt
            if value is None: return 0
            score = 100 * (min(value, max_val) / max_val)
            return max(0, score)
        return 0

    def calculate_for_property(self, property_id: int):
        print(f"[*] Calculating scores for Property ID: {property_id}")
        
        # 1. Lấy tọa độ BĐS từ PROPERTY DB
        query_prop = text("""
            SELECT ST_X(location::geometry) as lng, ST_Y(location::geometry) as lat 
            FROM properties WHERE id = :pid
        """)
        prop = self.db_prop.execute(query_prop, {"pid": property_id}).fetchone()
        
        if not prop:
            print(f"Error: Property {property_id} not found.")
            return

        prop_lng, prop_lat = prop.lng, prop.lat

        # 2. Tính toán từng chỉ số dựa trên AMENITY DB
        scores = {}
        raw_metrics = {} # Dictionary để lưu giá trị thô
        
        for key, config in CONSTANTS.items():
            categories = tuple(CATEGORY_MAPPING.get(key, [key]))
            
            if config['type'] == 'distance':
                # Query AMENITY DB: Tìm khoảng cách đến tiện ích gần nhất
                # Vì khác DB nên không JOIN được, ta truyền tọa độ vào ST_MakePoint
                sql = text("""
                    SELECT MIN(ST_Distance(
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 
                        location::geography
                    ))
                    FROM amenities
                    WHERE category IN :cats
                    AND ST_DWithin(
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 
                        location::geography, 
                        :max_dist
                    )
                """)
                result = self.scoring_db.execute(sql, {
                    "lng": prop_lng,
                    "lat": prop_lat,
                    "cats": categories,
                    "max_dist": config['max_dist'] * 2 
                }).scalar()
                
                raw_value = result if result is not None else float('inf')
                scores[f"score_{key}"] = self.normalize_score(raw_value, config['max_dist'], 'distance')
                raw_metrics[key] = result if result is not None else None

            elif config['type'] == 'count':
                # Query AMENITY DB: Đếm số lượng
                sql = text("""
                    SELECT COUNT(*)
                    FROM amenities
                    WHERE category IN :cats
                    AND ST_DWithin(
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 
                        location::geography, 
                        :radius
                    )
                """)
                count = self.scoring_db.execute(sql, {
                    "lng": prop_lng,
                    "lat": prop_lat,
                    "cats": categories,
                    "radius": config['radius']
                }).scalar()
                
                scores[f"score_{key}"] = self.normalize_score(count, config['max_count'], 'count')
                raw_metrics[key] = count

        # 3. Lưu kết quả vào PROPERTY DB
        score_record = self.scoring_db.query(PropertyLivabilityScore).filter_by(property_id=property_id).first()
        
        if not score_record:
            score_record = PropertyLivabilityScore(property_id=property_id)
            self.scoring_db.add(score_record)

        # Cập nhật điểm số
        score_record.score_healthcare = scores.get('score_healthcare', 0)
        score_record.score_education = scores.get('score_education', 0)
        score_record.score_shopping = scores.get('score_shopping', 0)
        score_record.score_transportation = scores.get('score_transportation', 0)
        score_record.score_environment = scores.get('score_environment', 0)
        score_record.score_entertainment = scores.get('score_entertainment', 0)
        score_record.score_safety = scores.get('score_public_safety', 0)

        # Cập nhật chỉ số thô
        score_record.dist_healthcare = raw_metrics.get('healthcare')
        score_record.dist_education = raw_metrics.get('education')
        score_record.count_shopping = raw_metrics.get('shopping')
        score_record.dist_transportation = raw_metrics.get('transportation')
        score_record.dist_environment = raw_metrics.get('environment')
        score_record.count_entertainment = raw_metrics.get('entertainment')
        score_record.dist_safety = raw_metrics.get('public_safety')

        self.scoring_db.commit()
        print(f"[OK] Scores updated for Property {property_id}: {scores}")