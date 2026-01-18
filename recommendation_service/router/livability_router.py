import os
import json
import jwt
import requests
from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

from dotenv import load_dotenv
from config.scoring_db_config import get_scoring_db
from model.livability_score import PropertyLivabilityScore
from schema.common import APIResponse, ResponseData
from schema.livability_schema import LivabilityScoreDTO, BatchScoreRequest

load_dotenv()

router = APIRouter(prefix="/api/v1/recommendation/livability", tags=["Livability Scores"])
security = HTTPBearer(auto_error=False) # Auto error = False để cho phép guest access

# --- CẤU HÌNH ---
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://kltn-user-service-be:8080")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Trọng số mặc định (Dùng khi không login hoặc chưa set profile)
DEFAULT_WEIGHTS = {
    'score_healthcare': 0.15,
    'score_education': 0.15,
    'score_shopping': 0.15,
    'score_transportation': 0.15,
    'score_environment': 0.15,
    'score_entertainment': 0.15,
    'score_safety': 0.10,
}

# --- HELPER: AUTHENTICATION ---
def get_current_user_id_optional(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[int]:
    """
    Lấy UserID từ Token nếu có. Nếu không (Guest), trả về None.
    """
    if not credentials:
        return None
    try:
        token = credentials.credentials
        # Verify Token (Giả định dùng chung Secret với User Service)
        payload = jwt.decode(
            token, 
            key=JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM], 
            options={"verify_exp": True}
        )
        
        # Parse payload đặc thù của dự án
        user_str = payload.get("user")
        if isinstance(user_str, str):
            user_data = json.loads(user_str)
            return user_data.get("userId")
        elif isinstance(user_str, dict):
            return user_str.get("userId")
    except Exception as e:
        print(f"Auth Warning: {e}")
        return None
    return None

# --- HELPER: FETCH USER PREFERENCES ---
def fetch_user_weights(user_id: int) -> Dict[str, float]:
    """
    Gọi Internal API sang User Service để lấy Preference.
    Normalize lại để tổng trọng số = 1.0.
    """
    if not user_id:
        return DEFAULT_WEIGHTS

    try:
        url = f"{USER_SERVICE_URL}/internal/user/{user_id}"
        # print(f"Fetching profile from: {url}")
        
        # Timeout nhỏ để không làm chậm request chính
        response = requests.get(url, timeout=2.0) 
        
        if response.status_code == 200:
            resp_json = response.json()
            # Giả định cấu trúc response: { "status": "200", "data": { ... } }
            data = resp_json.get("data")
            
            if not data:
                return DEFAULT_WEIGHTS

            # Mapping từ UserProfileResponse (Java) sang Scoring Keys (Python)
            # Dữ liệu từ Java BigDecimal sẽ được parse thành float
            raw_prefs = {
                'score_healthcare': float(data.get('preferenceHealthcare') or 0),
                'score_education': float(data.get('preferenceEducation') or 0),
                'score_shopping': float(data.get('preferenceShopping') or 0),
                'score_transportation': float(data.get('preferenceTransportation') or 0),
                'score_environment': float(data.get('preferenceEnvironment') or 0),
                'score_entertainment': float(data.get('preferenceEntertainment') or 0),
                'score_safety': float(data.get('preferenceSafety') or 0),
            }

            # Tính tổng điểm preference
            total_pref = sum(raw_prefs.values())

            # Nếu user chưa set gì (tổng = 0) -> Dùng mặc định
            if total_pref == 0:
                return DEFAULT_WEIGHTS

            # Normalize: Chia mỗi điểm cho tổng để đảm bảo tổng trọng số = 1.0
            normalized_weights = {k: v / total_pref for k, v in raw_prefs.items()}
            
            # print(f"User {user_id} custom weights: {normalized_weights}")
            return normalized_weights

    except Exception as e:
        print(f"Error fetching user weights from User Service: {e}")
        # Fallback về mặc định nếu lỗi mạng/service
        return DEFAULT_WEIGHTS
    
    return DEFAULT_WEIGHTS

# --- LOGIC TÍNH TOÁN ---
def calculate_overall_score(score_obj: PropertyLivabilityScore, weights: dict, include_special: bool = True) -> float:
    """
    Tính chỉ số sống dựa trên Mô hình Tổng hợp Đa tiêu chí có Hiệu chỉnh (Corrected Multi-Criteria Aggregation).
    """
    # 1. Chuẩn hóa trọng số (Normalized Weights)
    total_weight = sum(weights.values())
    if total_weight == 0: return 0.0
    w = {k: v / total_weight for k, v in weights.items()}

    def get_val(val): return float(val) if val is not None else 0.0

    # 2. Lấy dữ liệu điểm cơ sở (S1...S7) - Thang 0-100
    s_health = get_val(score_obj.score_healthcare)
    s_edu = get_val(score_obj.score_education)
    s_shop = get_val(score_obj.score_shopping)
    s_trans = get_val(score_obj.score_transportation)
    s_env = get_val(score_obj.score_environment)
    s_enter = get_val(score_obj.score_entertainment)
    s_safety = get_val(score_obj.score_safety)

    # 3. Xử lý Chỉ số đặc biệt (Special Indicators)
    # Bước 1: Hiệu chỉnh ngữ cảnh (Contextual Correction)
    potential_bonus = 0.0
    
    if include_special:
        # Lấy điểm phạt từ DB (Đã được chuẩn hóa về thang [0-10])
        p_flood = get_val(score_obj.flood_impact_score)       # Max 10
        p_accident = get_val(score_obj.accident_impact_score) # Max 10
        p_project = get_val(score_obj.future_project_score)   # Max 10 (Tiềm năng)
        
        # --- A. PHẠT (PENALTY) ---
        
        # 1. Giao thông (S'_trans): Chịu tác động kép
        # - Ngập lụt (Tê liệt chức năng): Hệ số Gamma = 2.0 (Max trừ 20đ)
        # - Tai nạn (Gián đoạn tạm thời): Hệ số Gamma = 0.5 (Max trừ 5đ)
        penalty_trans = (2.0 * p_flood) + (0.5 * p_accident)
        s_trans = max(0.0, s_trans - penalty_trans)

        # 2. Môi trường (S'_env): Chịu tác động thứ cấp
        # - Ngập lụt (Ô nhiễm): Hệ số Gamma = 1.0 (Max trừ 10đ)
        s_env = max(0.0, s_env - (1.0 * p_flood))

        # 3. An ninh (S'_safety): Chịu tác động tâm lý
        # - Tai nạn (Sợ hãi): Hệ số Gamma = 1.5 (Max trừ 15đ)
        s_safety = max(0.0, s_safety - (1.5 * p_accident))

        # --- B. THƯỞNG (BONUS) ---
        # Bước 3: Cộng thưởng Tiềm năng
        # Hệ số trọng số dự án Gamma_project = 1.0 (Max thưởng 10đ)
        potential_bonus = p_project * 1.0

    # 4. Bước 2: Tổng hợp theo trọng số người dùng (Weighted Sum Model)
    # Tính S_base
    base_score = (
        s_health * w.get('score_healthcare', 0) +
        s_edu * w.get('score_education', 0) +
        s_shop * w.get('score_shopping', 0) +
        s_trans * w.get('score_transportation', 0) + 
        s_env * w.get('score_environment', 0) +
        s_enter * w.get('score_entertainment', 0) +
        s_safety * w.get('score_safety', 0)
    )

    # 5. Cộng điểm tiềm năng
    final_score = base_score + potential_bonus

    # 6. Capping (Giới hạn [0-100])
    return round(min(100.0, max(0.0, final_score)), 2)

# --- API ENDPOINT ---
@router.post("/scores/batch", response_model=APIResponse[LivabilityScoreDTO])
def get_batch_livability_scores(
    payload: BatchScoreRequest,
    user_id: Optional[int] = Depends(get_current_user_id_optional),
    db: Session = Depends(get_scoring_db)
):
    try:
        if not payload.propertyIds:
            return APIResponse(status="200", result="Succeeded", data=ResponseData(items=[]))

        weights = fetch_user_weights(user_id) if user_id else DEFAULT_WEIGHTS

        scores = db.query(PropertyLivabilityScore).filter(
            PropertyLivabilityScore.property_id.in_(payload.propertyIds)
        ).all()

        results = []
        for score_record in scores:
            dto = LivabilityScoreDTO.model_validate(score_record)
            
            # Truyền thêm tham số include_special từ payload
            dto.livability_score = calculate_overall_score(
                score_record, 
                weights, 
                include_special=payload.include_special_factors
            )
            
            results.append(dto)

        return APIResponse(
            status="200",
            result="Succeeded",
            data=ResponseData(items=results)
        )

    except Exception as e:
        return APIResponse(status="500", result="Failed", error=str(e))