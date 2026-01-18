from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, cast, text
from geoalchemy2 import Geography
from typing import Optional, List, Dict, Set
from pydantic import BaseModel
from collections import Counter

from config.property_db_config import get_property_db
from config.scoring_db_config import get_scoring_db
from config.redis_config import redis_client
from model.property import Property
from model.livability_score import PropertyLivabilityScore
from router.livability_router import DEFAULT_WEIGHTS, fetch_user_weights
from schema.common import APIResponse, ResponseData
import json
router = APIRouter(prefix="/api/v1/recommendation", tags=["Recommendation"])

# --- Schema ---
class PropertyCard(BaseModel):
    id: int
    title: str
    price: float
    price_unit: str
    area: float
    address: str
    num_bedrooms: Optional[int]
    num_bathrooms: Optional[int]
    thumbnail_url: Optional[str]
    distance_km: float
    recommendation_type: str # LIVABILITY, PERSONALIZED, POPULARITY

    class Config:
        from_attributes = True

# --- Helper: Map Data ---
def map_to_schema(prop_obj, distance_meters, rec_type):
    full_addr = f"{prop_obj.address_street or ''}, {prop_obj.address_ward or ''}, {prop_obj.address_district or ''}"
    
    # Logic lấy ảnh thumbnail an toàn
    thumb = None
    # Kiểm tra nếu prop_obj.images là list object hay relationship
    if hasattr(prop_obj, 'images') and prop_obj.images:
        # Nếu là list object
        if len(prop_obj.images) > 0:
             # Giả sử model Image có field image_url
             thumb = prop_obj.images[0].image_url if hasattr(prop_obj.images[0], 'image_url') else None
    elif hasattr(prop_obj, 'source_url'):
        thumb = prop_obj.source_url

    return PropertyCard(
        id=prop_obj.id,
        title=prop_obj.title,
        price=float(prop_obj.price) if prop_obj.price else 0.0,
        price_unit=prop_obj.price_unit or "",
        area=float(prop_obj.area) if prop_obj.area else 0.0,
        address=full_addr,
        num_bedrooms=prop_obj.num_bedrooms,
        num_bathrooms=prop_obj.num_bathrooms,
        thumbnail_url=thumb,
        distance_km=round(distance_meters / 1000, 2) if distance_meters else 0.0,
        recommendation_type=rec_type
    )

@router.get("/home", response_model=APIResponse[PropertyCard])
def get_home_recommendations(
    lat: float = Query(..., description="Vĩ độ"),
    lng: float = Query(..., description="Kinh độ"),
    limit: int = Query(10, description="Tổng số lượng gợi ý cần lấy"),
    radius_km: float = Query(5.0, description="Bán kính tìm kiếm"),
    user_id: Optional[int] = Query(None),
    prop_db: Session = Depends(get_property_db),
    score_db: Session = Depends(get_scoring_db)
):
    try:
        # --- BƯỚC 0: CHECK REDIS CACHE (Chỉ nếu user đã login) ---
        cache_key = ""
        if user_id:
            # Làm tròn tọa độ 3 số lẻ (chính xác ~100m) để tăng cache hit khi GPS nhảy nhẹ
            lat_r = round(lat, 3)
            lng_r = round(lng, 3)
            cache_key = f"rec:home:result:{user_id}:{lat_r}:{lng_r}:{radius_km}:{limit}"
            
            cached_data = redis_client.get(cache_key)
            if cached_data:
                # Cache Hit! Deserialize và trả về ngay
                print(f"⚡ [CACHE HIT] User {user_id}")
                items_data = json.loads(cached_data)
                # Convert dict back to Pydantic models (optional, but good for validation)
                # items = [PropertyCard(**item) for item in items_data]
                return APIResponse(status="200", result="Succeeded", data=ResponseData(items=items_data))

        # --- TẦNG 1: KHOANH VÙNG KHÔNG GIAN (Spatial Filtering) ---
        # Lấy danh sách ứng viên sơ bộ (Candidates) từ DB Property
        # Lấy nhiều hơn limit (ví dụ 200) để có dữ liệu cho các tầng sau lọc và xếp hạng
        user_location = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
        
        # Chỉ lấy các trường cần thiết để tính toán (nhẹ DB)
        candidates_query = prop_db.query(
            Property.id, 
            Property.view_count, 
            Property.property_type, 
            Property.price,
            func.ST_Distance(
                cast(Property.location, Geography(srid=4326)), 
                cast(user_location, Geography(srid=4326))
            ).label("distance_meters")
        ).filter(
            func.ST_DWithin(
                cast(Property.location, Geography(srid=4326)), 
                cast(user_location, Geography(srid=4326)),
                radius_km * 1000
            )
        ).limit(200).all() # Lấy tối đa 200 ứng viên xung quanh

        if not candidates_query:
            return APIResponse(status="200", result="Succeeded", data=ResponseData(items=[]))

        # Convert sang list dict để dễ xử lý
        candidates = [
            {
                "id": c.id, 
                "view_count": c.view_count or 0, 
                "price": float(c.price or 0),
                "type": c.property_type,
                "dist": c.distance_meters,
                "livability_score": 0 # Sẽ điền sau
            } 
            for c in candidates_query
        ]
        candidate_ids = [c["id"] for c in candidates]
        candidate_map = {c["id"]: c for c in candidates}

 # --- TẦNG 2: ĐỊNH HƯỚNG CHẤT LƯỢNG SỐNG (Livability-First Calculation) ---
        # 1. Lấy Trọng số User (Realtime Preference)
        raw_weights = fetch_user_weights(user_id) if user_id else DEFAULT_WEIGHTS
        total_w = sum(raw_weights.values())
        # Chuẩn hóa trọng số
        w = {k: v / total_w for k, v in raw_weights.items()} if total_w > 0 else raw_weights

        # 2. Query DB lấy các chỉ số thành phần (Component Scores)
        score_records = score_db.query(PropertyLivabilityScore).filter(
            PropertyLivabilityScore.property_id.in_(candidate_ids)
        ).all()

        # 3. Tính toán điểm số theo Công thức Khóa luận
        for s in score_records:
            if s.property_id not in candidate_map: continue
            
            # Helper convert
            def get_val(v): return float(v or 0)

            # Lấy điểm gốc
            s_vals = {
                'score_healthcare': get_val(s.score_healthcare),
                'score_education': get_val(s.score_education),
                'score_shopping': get_val(s.score_shopping),
                'score_transportation': get_val(s.score_transportation),
                'score_environment': get_val(s.score_environment),
                'score_entertainment': get_val(s.score_entertainment),
                'score_safety': get_val(s.score_safety)
            }
            
            # Lấy điểm đặc biệt (Đã chuẩn hóa thang 10 trong DB)
            p_flood = get_val(s.flood_impact_score)
            p_accident = get_val(s.accident_impact_score)
            p_project = get_val(s.future_project_score)

            # --- ÁP DỤNG LOGIC PHẠT (PENALTY) ---
            # Giao thông: -2.0*Flood - 0.5*Accident
            s_vals['score_transportation'] = max(0.0, s_vals['score_transportation'] - (2.0 * p_flood + 0.5 * p_accident))
            
            # Môi trường: -1.0*Flood
            s_vals['score_environment'] = max(0.0, s_vals['score_environment'] - (1.0 * p_flood))
            
            # An ninh: -1.5*Accident
            s_vals['score_safety'] = max(0.0, s_vals['score_safety'] - (1.5 * p_accident))

            # --- TÍNH TỔNG CÓ TRỌNG SỐ (WEIGHTED SUM) ---
            base_score = sum(s_vals[k] * w.get(k, 0) for k in s_vals)

            # --- ÁP DỤNG THƯỞNG (BONUS) ---
            potential_bonus = p_project * 1.0
            
            final_score = base_score + potential_bonus
            
            # Cập nhật vào map
            candidate_map[s.property_id]["livability_score"] = round(min(100.0, max(0.0, final_score)), 2)

        # 4. Sắp xếp & Chọn lọc
        livability_quota = int(limit * 0.4)
        sorted_by_livability = sorted(candidates, key=lambda x: x["livability_score"], reverse=True)
        
        final_picks = []
        picked_ids = set()

        for cand in sorted_by_livability[:livability_quota]:
            cand["rec_type"] = "LIVABILITY"
            final_picks.append(cand)
            picked_ids.add(cand["id"])

        # --- TẦNG 3: CÁ NHÂN HÓA HÀNH VI (Redis) ---
        # Chỉ lấy từ Redis (Pre-computed Item-based CF)
        personalized_quota = int(limit * 0.4) # 40% tiếp theo
        
        if user_id:
            try:
                redis_key = f"rec:home:{user_id}"
                # Lấy danh sách ID từ Redis (Sorted Set, score càng cao càng phù hợp)
                # Lấy số lượng nhiều hơn quota một chút để bù trừ cho những ID không nằm trong bán kính
                cached_ids_bytes = redis_client.zrevrange(redis_key, 0, personalized_quota * 3) 
                redis_ids = [int(i) for i in cached_ids_bytes]
                
                count_personal = 0
                # Chỉ lấy những ID nào CŨNG nằm trong Spatial Candidates (Tầng 1)
                # Điều này đảm bảo tính "Local" của gợi ý
                for rid in redis_ids:
                    if rid in candidate_map and rid not in picked_ids:
                        cand = candidate_map[rid]
                        cand["rec_type"] = "PERSONALIZED"
                        final_picks.append(cand)
                        picked_ids.add(rid)
                        count_personal += 1
                        if count_personal >= personalized_quota:
                            break
            except Exception as e:
                print(f"Redis Error: {e}")

        # --- TẦNG 4: XU HƯỚNG ĐÁM ĐÔNG (Popularity Fallback) ---
        # Lấp đầy các slot còn trống bằng các căn có view cao nhất trong khu vực
        remaining_slots = limit - len(final_picks)
        
        if remaining_slots > 0:
            # Lọc những căn chưa được chọn
            remaining_candidates = [c for c in candidates if c["id"] not in picked_ids]
            
            # Sắp xếp theo lượt xem giảm dần
            sorted_by_view = sorted(remaining_candidates, key=lambda x: x["view_count"], reverse=True)
            
            for cand in sorted_by_view[:remaining_slots]:
                cand["rec_type"] = "POPULARITY"
                final_picks.append(cand)
                picked_ids.add(cand["id"])

        # --- FINAL FETCH: Lấy thông tin chi tiết ---
        # Lúc này ta mới query DB để lấy full thông tin (title, image...) cho đúng số lượng limit
        final_ids = [p["id"] for p in final_picks]
        
        # Query lấy full entity (đảm bảo thứ tự)
        full_props = prop_db.query(Property).filter(Property.id.in_(final_ids)).all()
        prop_map_obj = {p.id: p for p in full_props}
        
        result_cards = []
        for pick in final_picks:
            p_obj = prop_map_obj.get(pick["id"])
            if p_obj:
                card = map_to_schema(p_obj, pick["dist"], pick["rec_type"])
                result_cards.append(card)

        # --- BƯỚC CUỐI: SAVE TO REDIS CACHE (Chỉ nếu user đã login) ---
        if user_id and result_cards:
            try:
                # Serialize list Pydantic model sang List Dict -> JSON String
                json_data = [card.model_dump() for card in result_cards]
                # Set TTL 300 giây (5 phút)
                redis_client.setex(cache_key, 300, json.dumps(json_data))
                print(f"💾 [CACHE SAVED] User {user_id} - {len(result_cards)} items")
            except Exception as e:
                print(f"Cache Save Error: {e}")

        return APIResponse(
            status="200", 
            result="Succeeded", 
            data=ResponseData(items=result_cards)
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return APIResponse(status="500", result="Failed", error=str(e))