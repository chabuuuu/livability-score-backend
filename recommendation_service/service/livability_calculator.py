from sqlalchemy.orm import Session
from sqlalchemy import text

# --- CẤU HÌNH THAM SỐ ---
CONSTANTS = {
    'healthcare': {'max_dist': 1500, 'type': 'distance'},
    'education': {'max_dist': 1000, 'type': 'distance'},
    'transportation': {'max_dist': 500, 'type': 'distance'},
    'environment': {'max_dist': 1000, 'type': 'distance'}, 
    'public_safety': {'max_dist': 1000, 'type': 'distance'},
    'shopping': {'radius': 500, 'max_count': 15, 'type': 'count'},
    'entertainment': {'radius': 1000, 'max_count': 20, 'type': 'count'}
}

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
    def __init__(self, scoring_db: Session):
        """
        Chỉ cần kết nối tới DB chứa bảng amenities (scoring_db).
        Không cần db_prop vì không query/lưu property.
        """
        self.scoring_db = scoring_db

    def normalize_score(self, value, max_val, mode='distance'):
        """Chuẩn hóa điểm về thang 0-100."""
        if mode == 'distance':
            if value is None or value == float('inf'): return 0
            score = 100 * (1 - min(value, max_val) / max_val)
            return max(0, score)
        elif mode == 'count':
            if value is None: return 0
            score = 100 * (min(value, max_val) / max_val)
            return max(0, score)
        return 0

    def calculate_from_coordinates(self, lat: float, lng: float):
        """
        Tính toán điểm số Livability nóng (real-time) dựa trên tọa độ bất kỳ.
        Trả về: (scores_dict, raw_metrics_dict)
        """
        scores = {}
        raw_metrics = {} 
        
        for key, config in CONSTANTS.items():
            # Chuyển list category thành tuple để dùng trong SQL IN clause
            categories = tuple(CATEGORY_MAPPING.get(key, [key]))
            
            if config['type'] == 'distance':
                # Tìm khoảng cách ngắn nhất
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
                # max_dist * 2 để tìm rộng hơn một chút, tránh bỏ sót
                result = self.scoring_db.execute(sql, {
                    "lng": lng, "lat": lat,
                    "cats": categories, "max_dist": config['max_dist'] * 2 
                }).scalar()
                
                raw_value = result if result is not None else float('inf')
                scores[f"score_{key}"] = self.normalize_score(raw_value, config['max_dist'], 'distance')
                raw_metrics[key] = result if result is not None else None

            elif config['type'] == 'count':
                # Đếm số lượng
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
                    "lng": lng, "lat": lat,
                    "cats": categories, "radius": config['radius']
                }).scalar()
                
                scores[f"score_{key}"] = self.normalize_score(count, config['max_count'], 'count')
                raw_metrics[key] = count
        
        return scores, raw_metrics