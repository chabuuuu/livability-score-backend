# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# import pandas as pd
# import numpy as np

# from config.scoring_db_config import get_scoring_db
# from service.livability_calculator import LivabilityCalculator
# from schema.prediction_schema import PropertyPredictionRequest, PredictionResponse
# from service.model_loader import PriceModel
# from schema.common import APIDetailResponse, ResponseData

# router = APIRouter(prefix="/api/v1/recommendation/prediction", tags=["Price Prediction"])

# # --- FEATURE CONFIGURATION ---
# # Danh sách này PHẢI khớp chính xác thứ tự và tên cột lúc training model
# TRAINING_NUMERICAL_FEATURES = [
#     'area', 'num_bedrooms', 'num_bathrooms', 'num_floors',
#     'facade_width_m', 'road_width_m',
#     'score_healthcare', 'score_education', 'score_shopping',
#     'score_transportation', 'score_environment', 'score_entertainment',
#     'score_safety', 'livability_score'
# ]
# TRAINING_CATEGORICAL_FEATURES = [
#     'property_type', 'legal_status', 'house_direction',
#     'balcony_direction', 'furniture_status', 'address_district'
# ]
# ALL_TRAINING_FEATURES = TRAINING_NUMERICAL_FEATURES + TRAINING_CATEGORICAL_FEATURES

# # Trọng số tính điểm tổng hợp (Profile mặc định)
# DEFAULT_WEIGHTS = {
#     'score_healthcare': 0.15,
#     'score_education': 0.15,
#     'score_shopping': 0.15,
#     'score_transportation': 0.15,
#     'score_environment': 0.15,
#     'score_entertainment': 0.15,
#     'score_safety': 0.10,
# }

# @router.post("/property/price", response_model=APIDetailResponse[PredictionResponse])
# def predict_property_price(
#     payload: PropertyPredictionRequest,
#     scoring_db: Session = Depends(get_scoring_db)
# ):
#     """
#     API dự đoán giá nhà dựa trên thông tin người dùng nhập và chỉ số Livability Score tính toán realtime.
#     """
#     try:
#         # BƯỚC 1: TÍNH TOÁN LIVABILITY SCORE (Real-time từ tọa độ)
#         calculator = LivabilityCalculator(scoring_db=scoring_db)
        
#         # Tính các điểm thành phần (0-100)
#         component_scores, _ = calculator.calculate_from_coordinates(payload.latitude, payload.longitude)
        
#         # Tính điểm tổng hợp (Weighted Sum)
#         livability_score = 0.0
#         for key, weight in DEFAULT_WEIGHTS.items():
#             livability_score += component_scores.get(key, 0) * weight
        
#         # BƯỚC 2: CHUẨN BỊ DỮ LIỆU CHO MODEL AI
#         input_data = payload.model_dump()
        
#         # Merge điểm số vào input data
#         input_data.update(component_scores)
#         input_data['livability_score'] = livability_score
        
#         # Tạo DataFrame 1 dòng
#         df = pd.DataFrame([input_data])
        
#         # Xử lý các cột bị thiếu (điền NaN - Random Forest Pipeline thường tự handle hoặc cần Imputer)
#         # Đảm bảo DataFrame có đủ tất cả các cột như lúc train
#         for col in ALL_TRAINING_FEATURES:
#             if col not in df.columns:
#                 df[col] = np.nan
        
#         # Sắp xếp lại thứ tự cột cho đúng chuẩn
#         df_ordered = df[ALL_TRAINING_FEATURES]
        
#         # BƯỚC 3: GỌI MODEL DỰ ĐOÁN
#         predicted_price_vnd = PriceModel.predict(df_ordered)
        
#         # BƯỚC 4: TRẢ KẾT QUẢ
#         result = PredictionResponse(
#             predicted_price=round(predicted_price_vnd, 0),
#             predicted_price_billions=round(predicted_price_vnd / 1_000_000_000, 2),
#             livability_score=round(livability_score, 2),
#             component_scores=component_scores
#         )

#         return APIDetailResponse(
#             status="200",
#             result="Succeeded",
#             data=result
#         )

#     except Exception as e:
#         # Log lỗi chi tiết ra console server
#         import traceback
#         traceback.print_exc()
#         return APIDetailResponse(status="500", result="Failed", error=f"Prediction Error: {str(e)}")

import os
import json
import asyncio
import uuid # Để tạo Prediction ID
import jwt
from itertools import cycle
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import pandas as pd
import numpy as np
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from config.redis_config import redis_client

from config.scoring_db_config import get_scoring_db
from service.livability_calculator import LivabilityCalculator
from schema.prediction_schema import PropertyPredictionRequest, PredictionResponse
from service.model_loader import PriceModel
from schema.common import APIDetailResponse, APIResponse, ResponseData

# --- IMPORT CẤU HÌNH AI & AUTH TỪ ENV (Tương tự insight_router) ---
KEYS_STR = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in KEYS_STR.split(",") if k.strip()] or [os.getenv("GEMINI_API_KEY")]
key_cycle = cycle(API_KEYS)

def get_next_key():
    try: return next(key_cycle)
    except: raise Exception("No API Keys available")

FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite", 
    "gemini-robotics-er-1.5-preview"
]
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

router = APIRouter(prefix="/api/v1/prediction", tags=["Price Prediction"])
security = HTTPBearer()

# --- HELPER: AUTHENTICATION ---
def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> int:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": True})
        user_str = payload.get("user")
        if isinstance(user_str, str): return json.loads(user_str).get("userId")
        elif isinstance(user_str, dict): return user_str.get("userId")
        return 0
    except:
        return 0 # Cho phép Guest dùng nhưng sẽ không lưu history chat lâu dài được

# --- HELPER: GET AMENITIES CONTEXT BY COORDS (MỚI) ---
def get_amenities_context_by_coords(db: Session, lat: float, lng: float):
    """
    Truy vấn tên các tiện ích xung quanh tọa độ (cho BĐS chưa lưu trong DB).
    """
    sql = text("""
        WITH ranked_amenities AS (
            SELECT category, name,
                ST_Distance(location::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) as dist_m,
                google_rating,
                ROW_NUMBER() OVER (PARTITION BY category ORDER BY location <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)) as rn
            FROM amenities
            WHERE category IN ('healthcare', 'education', 'shopping', 'transportation', 'environment')
            AND ST_DWithin(location::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, 2000)
        )
        SELECT category, name, dist_m, google_rating FROM ranked_amenities WHERE rn <= 2;
    """)
    
    results = db.execute(sql, {"lat": lat, "lng": lng}).fetchall()
    
    grouped = {cat: [] for cat in ['healthcare', 'education', 'shopping', 'transportation', 'environment']}
    for row in results:
        grouped[row.category].append(f"- {row.name} ({int(row.dist_m)}m, {row.google_rating or 'N/A'}*)")
    
    return {k: "\n".join(v) if v else "Không tìm thấy gần đây" for k, v in grouped.items()}

# --- HELPER: CALL AI (SYNC VERSION FOR PREDICTION) ---
# Vì API dự đoán trả về JSON (không stream), ta dùng hàm sync await để lấy full text
async def generate_insight_text(prompt: str):
    last_error = None
    for model_name in FALLBACK_MODELS:
        try:
            current_key = get_next_key()
            genai.configure(api_key=current_key)
            model = genai.GenerativeModel(model_name=model_name)
            
            # Gọi hàm generate_content_async (không stream) để lấy toàn bộ text
            response = await model.generate_content_async(prompt)
            return response.text
        except google_exceptions.ResourceExhausted:
            continue
        except Exception as e:
            last_error = e
            break
    return "Hiện tại AI đang bận, không thể phân tích chi tiết."

# --- FEATURE CONFIG ---
TRAINING_NUMERICAL_FEATURES = [
    'area', 'num_bedrooms', 'num_bathrooms', 'num_floors',
    'facade_width_m', 'road_width_m',
    'score_healthcare', 'score_education', 'score_shopping',
    'score_transportation', 'score_environment', 'score_entertainment',
    'score_safety', 'livability_score'
]
TRAINING_CATEGORICAL_FEATURES = [
    'property_type', 'legal_status', 'house_direction',
    'balcony_direction', 'furniture_status', 'address_district'
]
ALL_TRAINING_FEATURES = TRAINING_NUMERICAL_FEATURES + TRAINING_CATEGORICAL_FEATURES

WEIGHTS = {
    'score_healthcare': 0.15, 'score_education': 0.15, 'score_shopping': 0.15,
    'score_transportation': 0.15, 'score_environment': 0.15, 'score_entertainment': 0.15, 'score_safety': 0.10
}

@router.post("/price", response_model=APIDetailResponse[PredictionResponse])
async def predict_property_price(
    payload: PropertyPredictionRequest,
    user_id: int = Depends(get_current_user_id),
    scoring_db: Session = Depends(get_scoring_db)
):
    try:
        # 1. Tính Livability Score (Realtime)
        calculator = LivabilityCalculator(scoring_db=scoring_db)
        scores, _ = calculator.calculate_from_coordinates(payload.latitude, payload.longitude)
        
        total_livability = 0.0
        for key, weight in WEIGHTS.items():
            total_livability += scores.get(key, 0) * weight
        
        # 2. Dự đoán giá (AI Model)
        input_data = payload.model_dump()
        input_data.update(scores)
        input_data['livability_score'] = total_livability
        
        df = pd.DataFrame([input_data])
        for col in ALL_TRAINING_FEATURES:
            if col not in df.columns: df[col] = np.nan
        df_ordered = df[ALL_TRAINING_FEATURES]
        
        predicted_price = PriceModel.predict(df_ordered)
        price_billions = predicted_price / 1_000_000_000

        # 3. Lấy Context Tiện ích thực tế (Để AI chém gió có cơ sở)
        amenity_context = get_amenities_context_by_coords(scoring_db, payload.latitude, payload.longitude)

        # 4. Tạo Prompt cho Gemini
        ai_prompt = f"""
        Bạn là chuyên gia định giá Bất động sản. Hãy giải thích tại sao căn nhà này có giá dự đoán là {price_billions:,.2f} tỷ VNĐ.
        
        --- THÔNG TIN CĂN NHÀ ---
        - Vị trí: {payload.address_district} (Lat: {payload.latitude}, Lng: {payload.longitude})
        - Diện tích: {payload.area}m2, {payload.num_floors} tầng.
        - Kết cấu: {payload.num_bedrooms} ngủ, {payload.num_bathrooms} vệ sinh.
        - Mặt tiền: {payload.facade_width_m}m, Đường trước nhà: {payload.road_width_m}m.
        - Loại: {payload.property_type}, Nội thất: {payload.furniture_status}.
        
        --- CHỈ SỐ SỐNG (0-100) ---
        - Tổng hợp: {total_livability:.1f}/100 (Rất quan trọng)
        - Y tế: {scores.get('score_healthcare')}, Giáo dục: {scores.get('score_education')}
        - Tiện ích: {scores.get('score_shopping')}, Môi trường: {scores.get('score_environment')}
        - An ninh: {scores.get('score_safety')}

        --- TIỆN ÍCH LÂN CẬN (CONTEXT THỰC TẾ) ---
        - Y tế: {amenity_context.get('healthcare')}
        - Giáo dục: {amenity_context.get('education')}
        - Mua sắm: {amenity_context.get('shopping')}
        - Môi trường: {amenity_context.get('environment')}

        --- YÊU CẦU ---
        Viết một đoạn phân tích ngắn (khoảng 150 từ), giọng chuyên gia, sắc sảo:
        1. Nhận xét mức giá này là cao hay thấp so với đặc điểm (ví dụ: nhà hẻm nhưng giá cao do gần trung tâm/tiện ích?).
        2. Chỉ ra các yếu tố "đắt giá" nhất (ví dụ: mặt tiền rộng, gần Vincom, điểm An ninh cao...).
        3. Chỉ ra điểm trừ (nếu có).
        """

        # 5. Gọi Gemini (Async)
        ai_insight_text = await generate_insight_text(ai_prompt)

        # 6. Lưu vào Cache Chat History (Để user hỏi tiếp)
        # Tạo ID phiên dự đoán
        prediction_id = str(uuid.uuid4())
        
        # Key cache đặc biệt cho Prediction Chat: rec:chat:prediction:{uuid}:{user_id}
        chat_history_key = f"rec:chat:prediction:{prediction_id}:{user_id}"
        
        # Tạo history ban đầu
        initial_history = [
            {"role": "system_context", "text": ai_prompt}, # Lưu prompt gốc làm context ẩn
            {"role": "model", "text": ai_insight_text}
        ]
        redis_client.setex(chat_history_key, 86400, json.dumps(initial_history))

        # 7. Trả kết quả
        result = PredictionResponse(
            prediction_id=prediction_id,
            predicted_price=round(predicted_price, 0),
            predicted_price_billions=round(price_billions, 2),
            livability_score=round(total_livability, 2),
            component_scores=scores,
            ai_insight=ai_insight_text
        )

        return APIDetailResponse(
            status="200",
            result="Succeeded",
            data=result
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return APIDetailResponse(status="500", result="Failed", error=f"Error: {str(e)}")