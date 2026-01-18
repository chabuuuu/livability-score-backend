from sqlalchemy.orm import Session
from sqlalchemy import text
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

class LivabilityCalculator:
    def __init__(self, scoring_db: Session):
        self.scoring_db = scoring_db

    def normalize_score(self, value, max_val, mode='distance'):
        """Chuẩn hóa điểm về thang 0-100."""
        if mode == 'distance':
            # Hàm suy giảm tuyến tính (Linear Decay)
            if value is None or value == float('inf') or value > max_val: 
                return 0.0
            score = 100 * (1 - value / max_val)
            return round(max(0.0, score), 2)
            
        elif mode == 'count':
            # Hàm bão hòa (Density Saturation)
            if value is None: 
                return 0.0
            score = 100 * min(1, value / max_val)
            return round(max(0.0, score), 2)
        return 0.0

    def get_district_stats(self, lat: float, lng: float):
        """
        Truy vấn không gian để lấy Chỉ số đặc biệt của Quận.
        Trả về: dict (flood, accident, project) chuẩn hóa thang 10.
        """
        sql = text("""
            SELECT 
                flood_impact_score, 
                accident_impact_score, 
                future_project_score
            FROM district_special_stats
            WHERE boundary IS NOT NULL
            AND ST_Within(
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), 
                boundary
            )
            LIMIT 1
        """)
        
        row = self.scoring_db.execute(sql, {"lng": lng, "lat": lat}).fetchone()
        
        if row:
            return {
                "flood_impact_score": float(row.flood_impact_score or 0),
                "accident_impact_score": float(row.accident_impact_score or 0),
                "future_project_score": float(row.future_project_score or 0)
            }
        else:
            return {
                "flood_impact_score": 0.0,
                "accident_impact_score": 0.0,
                "future_project_score": 0.0
            }

    def calculate_from_coordinates(self, lat: float, lng: float):
        """
        Tính toán toàn bộ các chỉ số Livability (7 chỉ số tĩnh Hybrid + 3 chỉ số động)
        cho một tọa độ bất kỳ (Real-time Calculation).
        """
        scores = {}
        raw_metrics = {} 
        
        # 1. Tính 7 chỉ số thành phần cơ bản (Base Scores) theo công thức Hybrid
        for key, config in CONSTANTS.items():
            # key chính là category trong DB (vd: 'healthcare', 'shopping'...)
            
            # Bán kính quét tối đa để query DB (lấy max giữa khoảng cách và bán kính mật độ)
            search_bound = max(config['max_dist'], config['radius']) * 1.5
            
            # --- SINGLE UNIFIED QUERY ---
            # Truy vấn 1 lần lấy cả Min Distance và Density Count
            sql = text("""
                SELECT 
                    MIN(ST_Distance(
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 
                        location::geography
                    )) as min_dist,
                    COUNT(*) FILTER (WHERE ST_DWithin(
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 
                        location::geography, 
                        :count_radius
                    )) as density_count
                FROM amenities
                WHERE category = :target_cat 
                AND ST_DWithin(
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 
                    location::geography, 
                    :search_bound
                )
            """)
            
            result = self.scoring_db.execute(sql, {
                "lng": lng, "lat": lat,
                "target_cat": key,
                "count_radius": config['radius'],
                "search_bound": search_bound
            }).fetchone()
            
            # Xử lý dữ liệu thô
            raw_dist = result.min_dist if result and result.min_dist is not None else float('inf')
            raw_count = result.density_count if result and result.density_count is not None else 0
            
            # --- TÍNH ĐIỂM HYBRID ---
            # 1. Điểm Khoảng cách (S_dist)
            s_dist = self.normalize_score(raw_dist, config['max_dist'], 'distance')
            
            # 2. Điểm Mật độ (S_count)
            s_count = self.normalize_score(raw_count, config['max_count'], 'count')
            
            # 3. Tổng hợp theo trọng số Alpha
            alpha = config['alpha']
            final_score = (alpha * s_dist) + ((1 - alpha) * s_count)
            
            # Mapping key trả về đúng format (score_healthcare, ...)
            if key == 'public_safety':
                scores["score_safety"] = round(final_score, 2)
                raw_metrics["dist_safety"] = raw_dist if raw_dist != float('inf') else None
                raw_metrics["count_safety"] = raw_count
                
            elif key == 'transportation':
                scores["score_transportation"] = round(final_score, 2)
                raw_metrics["dist_transport"] = raw_dist if raw_dist != float('inf') else None
                raw_metrics["count_transport"] = raw_count
                
            else:
                # Các key khác: healthcare, education, shopping, entertainment, environment
                scores[f"score_{key}"] = round(final_score, 2)
                raw_metrics[f"dist_{key}"] = raw_dist if raw_dist != float('inf') else None
                raw_metrics[f"count_{key}"] = raw_count

        # 2. Lấy 3 chỉ số đặc biệt từ Quận (Special Indicators)
        district_stats = self.get_district_stats(lat, lng)
        
        # Merge kết quả
        scores.update(district_stats)
        
        return scores, raw_metrics