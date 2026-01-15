from sqlalchemy.orm import Session
from sqlalchemy import text

from model.PropertyLivabilityScore import PropertyLivabilityScore

# --- HYBRID CONFIGURATION ---
# alpha: Trọng số cho khoảng cách (0.7 nghĩa là 70% khoảng cách, 30% mật độ)
# radius: Bán kính dùng để đếm số lượng tiện ích (Count)
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
    def __init__(self, db_prop: Session, scoring_db: Session):
        self.db_prop = db_prop
        self.scoring_db = scoring_db

    def normalize_score(self, value, max_val, mode='distance'):
        """Chuẩn hóa điểm về 0-100"""
        if mode == 'distance':
            # Hàm suy giảm tuyến tính
            if value is None or value == float('inf') or value > max_val: 
                return 0
            return 100 * (1 - value / max_val)
            
        elif mode == 'count':
            # Hàm bão hòa
            if value is None: 
                return 0
            return 100 * min(1, value / max_val)
        return 0

    def calculate_for_property(self, property_id: int, auto_commit=True):
        print(f"[*] Calculating Hybrid Scores for Property ID: {property_id}")
        
        # 1. Lấy tọa độ BĐS
        query_prop = text("""
            SELECT ST_X(location::geometry) as lng, ST_Y(location::geometry) as lat 
            FROM properties WHERE id = :pid
        """)
        prop = self.db_prop.execute(query_prop, {"pid": property_id}).fetchone()
        
        if not prop:
            print(f"Error: Property {property_id} not found.")
            return

        prop_lng, prop_lat = prop.lng, prop.lat

        # 2. Tính toán điểm số Hybrid
        scores = {}
        raw_dist_metrics = {}  
        raw_count_metrics = {} 
        
        for category_name, config in CONSTANTS.items():
            # category_name chính là giá trị trong cột 'category' (ví dụ: 'healthcare')
            
            # Bán kính quét tối đa để query DB (lấy max giữa khoảng cách và bán kính mật độ)
            search_bound = max(config['max_dist'], config['radius']) * 1.5 
            
            # --- SINGLE UNIFIED QUERY (Đã sửa lại WHERE category = ...) ---
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
                WHERE category = :target_cat  -- <--- SỬA Ở ĐÂY: So sánh trực tiếp
                AND ST_DWithin(
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 
                    location::geography, 
                    :search_bound
                )
            """)
            
            result = self.scoring_db.execute(sql, {
                "lng": prop_lng,
                "lat": prop_lat,
                "target_cat": category_name,
                "count_radius": config['radius'],
                "search_bound": search_bound
            }).fetchone()
            
            # Xử lý kết quả thô
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
            
            scores[f"score_{category_name}"] = final_score
            
            # Lưu giá trị thô
            raw_dist_metrics[category_name] = raw_dist if raw_dist != float('inf') else None
            raw_count_metrics[category_name] = raw_count

        # 3. Lưu kết quả vào PROPERTY DB
        score_record = self.scoring_db.query(PropertyLivabilityScore).filter_by(property_id=property_id).first()
        
        if not score_record:
            score_record = PropertyLivabilityScore(property_id=property_id)
            self.scoring_db.add(score_record)

        # Cập nhật điểm số chuẩn hóa
        score_record.score_healthcare = scores.get('score_healthcare', 0)
        score_record.score_education = scores.get('score_education', 0)
        score_record.score_shopping = scores.get('score_shopping', 0)
        score_record.score_transportation = scores.get('score_transportation', 0)
        score_record.score_environment = scores.get('score_environment', 0)
        score_record.score_entertainment = scores.get('score_entertainment', 0)
        score_record.score_safety = scores.get('score_public_safety', 0) 

        # Cập nhật chỉ số thô (Raw Metrics)
        score_record.dist_healthcare = raw_dist_metrics.get('healthcare')
        score_record.dist_education = raw_dist_metrics.get('education')
        score_record.dist_transportation = raw_dist_metrics.get('transportation')
        score_record.dist_environment = raw_dist_metrics.get('environment')
        score_record.dist_safety = raw_dist_metrics.get('public_safety')
        score_record.dist_entertainment = raw_dist_metrics.get('entertainment')
        score_record.dist_shopping = raw_dist_metrics.get('shopping')
        
        score_record.count_shopping = raw_count_metrics.get('shopping')
        score_record.count_entertainment = raw_count_metrics.get('entertainment')
        score_record.count_healthcare = raw_count_metrics.get('healthcare')
        score_record.count_education = raw_count_metrics.get('education')
        score_record.count_transportation = raw_count_metrics.get('transportation')
        score_record.count_environment = raw_count_metrics.get('environment')
        score_record.count_safety = raw_count_metrics.get('public_safety')

        if auto_commit:
            self.scoring_db.commit()
            print(f"[OK] Scores updated for Property {property_id}")
        else:
            # Nếu không commit, ta chỉ flush để object có trong session transaction hiện tại
            # flush giúp giải phóng bộ nhớ nhẹ nhưng chưa ghi xuống đĩa cứng
            self.scoring_db.flush()