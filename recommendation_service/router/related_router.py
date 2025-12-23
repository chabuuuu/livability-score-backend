import os
import json
import numpy as np
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from geoalchemy2 import Geography
from typing import Optional, List, Dict

# Import Config & Models
from config.property_db_config import get_property_db
from config.scoring_db_config import get_scoring_db
from model.property import Property
from model.livability_score import PropertyLivabilityScore
from schema.common import APIResponse, ResponseData

# Tái sử dụng logic lấy user weight từ livability router
from router.livability_router import fetch_user_weights, DEFAULT_WEIGHTS, get_current_user_id_optional

# Reuse Schema PropertyCard (hoặc import từ file schema chung)
from pydantic import BaseModel
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
    recommendation_type: str
    view_count: Optional[int] = 0
    match_score: Optional[float] = 0.0 # Điểm phù hợp (0-100)

    class Config:
        from_attributes = True

router = APIRouter(prefix="/api/v1/recommendation/related", tags=["Related Properties"])

# --- THUẬT TOÁN 1: CONTENT-BASED SIMILARITY ---
def calculate_content_similarity(target: Property, candidate: Property) -> float:
    """
    So sánh độ giống nhau về mặt vật lý giữa 2 căn nhà.
    Output: 0.0 -> 1.0
    """
    score = 0.0
    
    # 1. Price Similarity (Trọng số cao nhất: 0.4)
    # Công thức: 1 - |giá_1 - giá_2| / max(giá_1, giá_2)
    try:
        p1, p2 = float(target.price), float(candidate.price)
        if p1 > 0 and p2 > 0:
            price_sim = 1 - abs(p1 - p2) / max(p1, p2)
            score += max(0, price_sim) * 0.4
    except: pass

    # 2. Area Similarity (Trọng số: 0.3)
    try:
        a1, a2 = float(target.area), float(candidate.area)
        if a1 > 0 and a2 > 0:
            area_sim = 1 - abs(a1 - a2) / max(a1, a2)
            score += max(0, area_sim) * 0.3
    except: pass

    # 3. Bedroom Match (Trọng số: 0.15)
    if target.num_bedrooms == candidate.num_bedrooms:
        score += 0.15
    elif abs((target.num_bedrooms or 0) - (candidate.num_bedrooms or 0)) <= 1:
        score += 0.05 # Chênh lệch 1 phòng vẫn chấp nhận được

    # 4. Property Type Match (Trọng số: 0.15)
    if target.property_type == candidate.property_type:
        score += 0.15
        
    return score

# --- THUẬT TOÁN 2: PREFERENCE MATCHING ---
def calculate_preference_match(score_obj: PropertyLivabilityScore, weights: Dict[str, float]) -> float:
    """
    So sánh điểm sống của căn nhà với sở thích của User.
    Output: 0.0 -> 1.0
    """
    if not score_obj: return 0.5 # Neutral score nếu chưa có dữ liệu
    
    match_score = 0.0
    
    # Tính tổng có trọng số (Weighted Sum)
    # Các score_* trong DB là thang 0-100
    def get_s(val): return float(val) if val is not None else 0.0
    
    match_score += get_s(score_obj.score_healthcare) * weights.get('score_healthcare', 0)
    match_score += get_s(score_obj.score_education) * weights.get('score_education', 0)
    match_score += get_s(score_obj.score_shopping) * weights.get('score_shopping', 0)
    match_score += get_s(score_obj.score_transportation) * weights.get('score_transportation', 0)
    match_score += get_s(score_obj.score_environment) * weights.get('score_environment', 0)
    match_score += get_s(score_obj.score_entertainment) * weights.get('score_entertainment', 0)
    match_score += get_s(score_obj.score_safety) * weights.get('score_safety', 0)
    
    # Normalize về 0-1
    return match_score / 100.0

# --- API ENDPOINT ---
@router.get("/{property_id}", response_model=APIResponse[PropertyCard])
def get_related_properties(
    property_id: int,
    limit: int = Query(6, description="Số lượng gợi ý"),
    radius_km: float = Query(3.0, description="Bán kính tìm kiếm (km)"),
    user_id: Optional[int] = Depends(get_current_user_id_optional),
    property_db: Session = Depends(get_property_db),
    scoring_db: Session = Depends(get_scoring_db)
):
    try:
        # BƯỚC 1: LẤY THÔNG TIN BĐS ĐANG XEM (TARGET)
        target_prop = property_db.query(Property).filter(Property.id == property_id).first()
        if not target_prop:
            raise HTTPException(status_code=404, detail="Property not found")
        
        print("Target Property:", target_prop.id, target_prop.title)

        # BƯỚC 2: LẤY TRỌNG SỐ NGƯỜI DÙNG (PERSONALIZATION)
        # Gọi User Service (nếu có user_id) hoặc dùng mặc định
        user_weights = fetch_user_weights(user_id) if user_id else DEFAULT_WEIGHTS

        print("User Weights:", user_weights)

        # BƯỚC 3: LỌC ỨNG VIÊN (CANDIDATE GENERATION - Spatial Filter)
        # Tìm những căn nhà gần đó và giá không quá chênh lệch (+- 40%)
        # Đây là bước lọc thô để giảm tải tính toán
        min_price = float(target_prop.price) * 0.6
        max_price = float(target_prop.price) * 1.4

        print(f"Finding candidates within {radius_km} km, price range {min_price}-{max_price}")

        print("Target Property Location:", target_prop.location)
        
        target_loc_hex = str(target_prop.location)
        target_geom_expr = func.ST_GeomFromEWKB(func.decode(target_loc_hex, 'hex'))
        
        candidates = property_db.query(
            Property,
            func.ST_Distance(
                cast(Property.location, Geography(srid=4326)),
                cast(target_geom_expr, Geography(srid=4326))
            ).label("distance_meters")
        ).filter(
            Property.id != property_id,
            Property.price >= min_price,
            Property.price <= max_price,
            func.ST_DWithin(
                cast(Property.location, Geography(srid=4326)),
                cast(target_geom_expr, Geography(srid=4326)),
                radius_km * 1000
            )
        ).limit(100).all() # Lấy 100 ứng viên để tính điểm và rank lại

        if not candidates:
            return APIResponse(status="200", result="Succeeded", data=ResponseData(items=[]))

        # Lấy danh sách ID ứng viên để query điểm sống
        candidate_ids = [c.Property.id for c in candidates]

        # BƯỚC 4: LẤY LIVABILITY SCORE CỦA CÁC ỨNG VIÊN (SCORING DB)
        scores_map = {}
        score_records = scoring_db.query(PropertyLivabilityScore).filter(
            PropertyLivabilityScore.property_id.in_(candidate_ids)
        ).all()
        for s in score_records:
            scores_map[s.property_id] = s

        # BƯỚC 5: TÍNH ĐIỂM HYBRID VÀ XẾP HẠNG (RANKING)
        ranked_candidates = []
        
        for cand_prop, dist_m in candidates:
            # A. Content Similarity (0.0 - 1.0) -> Độ giống nhà cũ
            content_score = calculate_content_similarity(target_prop, cand_prop)
            
            # B. Preference Match (0.0 - 1.0) -> Độ hợp gu User
            livability_record = scores_map.get(cand_prop.id)
            pref_score = calculate_preference_match(livability_record, user_weights)
            
            # C. Collaborative/Popularity Boost (0.0 - 0.2) -> Độ Hot cộng đồng
            # Dùng logarit của view_count để chuẩn hóa (tránh số quá lớn lấn át)
            # Ví dụ: view=100 -> log10(100)=2 -> *0.05 = 0.1 điểm cộng
            view_boost = min(np.log10(cand_prop.view_count + 1) * 0.05, 0.2)
            
            # --- TỔNG HỢP ---
            # 40% Giống nhau + 40% Hợp gu + 20% Hot/Gần
            # Có thể điều chỉnh hệ số này
            final_score = (0.4 * content_score) + (0.4 * pref_score) + view_boost
            
            ranked_candidates.append({
                "prop": cand_prop,
                "dist": dist_m,
                "score": final_score
            })

        # Sắp xếp giảm dần theo điểm
        ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        # BƯỚC 6: FORMAT KẾT QUẢ
        final_items = []
        for item in ranked_candidates[:limit]:
            p = item["prop"]

            thumb = None 
            
            # Kiểm tra xem list images có tồn tại và có phần tử không
            if p.images and len(p.images) > 0:
                thumb = p.images[0].image_url
            else:
                thumb = None

            card = PropertyCard(
                id=p.id,
                title=p.title,
                price=float(p.price),
                price_unit=p.price_unit,
                area=float(p.area),
                address=f"{p.address_street or ''}, {p.address_district or ''}",
                num_bedrooms=p.num_bedrooms,
                num_bathrooms=p.num_bathrooms,
                thumbnail_url=thumb,
                distance_km=round(item["dist"] / 1000, 2),
                recommendation_type="HYBRID_RELATED",
                view_count=p.view_count,
                match_score=round(item["score"] * 100, 1) # Hiển thị độ phù hợp %
            )
            final_items.append(card)

        return APIResponse(
            status="200",
            result="Succeeded",
            data=ResponseData(items=final_items)
        )

    except Exception as e:
        # import traceback; traceback.print_exc()
        return APIResponse(status="500", result="Failed", error=str(e))