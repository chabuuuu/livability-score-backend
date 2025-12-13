import os
import json
import asyncio
import uuid # Để tạo Prediction ID
from fastapi.responses import StreamingResponse
import jwt
from itertools import cycle
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import pandas as pd
import numpy as np
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from config.redis_config import redis_client

from config.scoring_db_config import get_scoring_db
from service.livability_calculator import LivabilityCalculator
from schema.prediction_schema import ChatMessageDTO, ChatPredictionRequest, PropertyPredictionRequest, PredictionResponse
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

router = APIRouter(prefix="/api/v1/recommendation/prediction", tags=["Price Prediction"])
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
        print(f"Trying to call Gemini model: {model_name}")
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

@router.post("/property/price", response_model=APIDetailResponse[PredictionResponse])
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

        print("Prompt for AI Insight:", ai_prompt)

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
    
async def generate_content_smart(prompt: str):
    """Logic retry model & key tự động cho streaming"""
    last_error = None
    for model_name in FALLBACK_MODELS:
        # Thử tối đa 2 key cho mỗi model
        for _ in range(2):
            try:
                current_key = get_next_key()
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel(model_name=model_name)
                
                response = await model.generate_content_async(prompt, stream=True)
                async for chunk in response:
                    yield chunk
                return 
            except google_exceptions.ResourceExhausted:
                continue # Đổi key/model
            except Exception as e:
                last_error = e
                break # Lỗi khác thì đổi model luôn
    raise last_error if last_error else Exception("AI Overloaded")

# --- CHAT FOLLOW-UP --
@router.post("/property/chat/stream")
async def chat_prediction_stream(
    payload: ChatPredictionRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Cho phép user chat tiếp về kết quả dự đoán vừa nhận được.
    Yêu cầu: prediction_id hợp lệ (vẫn còn trong Redis).
    """
    prediction_id = payload.prediction_id
    user_message = payload.message
    
    # 1. Lấy lịch sử từ Redis
    chat_key = f"rec:chat:prediction:{prediction_id}:{user_id}"
    history_data = redis_client.get(chat_key)
    
    if not history_data:
        # Trường hợp hết hạn cache hoặc ID sai
        async def error_stream():
            yield json.dumps({"type": "error", "message": "Phiên dự đoán đã hết hạn hoặc không tồn tại."}) + "\n"
        return StreamingResponse(error_stream(), media_type="application/x-ndjson")

    chat_history = json.loads(history_data)
    
    # 2. Xây dựng Prompt
    # Lấy system context (thông tin nhà) từ tin nhắn đầu tiên
    system_context = chat_history[0]['text'] if chat_history else ""
    
    # Lấy các tin nhắn gần nhất để AI nhớ hội thoại
    recent_history_str = ""
    for msg in chat_history[-6:]: # Lấy 3 cặp gần nhất
        role = "AI" if msg['role'] == 'model' else "Khách hàng"
        if msg['role'] != 'system_context':
            recent_history_str += f"- {role}: {msg['text']}\n"

    chat_prompt = f"""
    Bạn là chuyên gia tư vấn BĐS đang hỗ trợ khách hàng.
    
    --- THÔNG TIN CĂN NHÀ ĐANG THẢO LUẬN (Context gốc) ---
    {system_context}

    --- LỊCH SỬ HỘI THOẠI ---
    {recent_history_str}

    --- CÂU HỎI MỚI ---
    Khách hàng: "{user_message}"

    --- YÊU CẦU ---
    Trả lời ngắn gọn, chuyên nghiệp. Giải thích dựa trên dữ liệu căn nhà (diện tích, vị trí, tiện ích...).
    Nếu khách hỏi về giá, hãy bảo vệ quan điểm định giá của hệ thống nhưng vẫn gợi mở các yếu tố có thể thương lượng.
    """

    # 3. Stream Response
    async def generate_chat_stream():
        full_response = ""
        try:
            async for chunk in generate_content_smart(chat_prompt):
                if chunk.text:
                    yield json.dumps({"type": "content", "text": chunk.text}) + "\n"
                    full_response += chunk.text
            
            # 4. Cập nhật Redis
            if full_response:
                chat_history.append({"role": "user", "text": user_message})
                chat_history.append({"role": "model", "text": full_response})
                # Giữ lại tối đa 20 tin (bao gồm cả system context ở đầu)
                # Đảm bảo phần tử đầu tiên (context) luôn được giữ
                updated_history = [chat_history[0]] + chat_history[-19:]
                
                redis_client.setex(chat_key, 86400, json.dumps(updated_history))
                
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(generate_chat_stream(), media_type="application/x-ndjson")

# --- API 3: GET CHAT HISTORY ---
@router.get("/property/chat/history/{prediction_id}", response_model=APIResponse[ChatMessageDTO])
async def get_chat_history(
    prediction_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Lấy toàn bộ lịch sử chat của phiên dự đoán này từ Redis.
    """
    try:
        chat_key = f"rec:chat:prediction:{prediction_id}:{user_id}"
        history_data = redis_client.get(chat_key)
        
        items = []
        if history_data:
            raw_history = json.loads(history_data)
            # Loại bỏ system context khỏi lịch sử trả về cho user
            items = [
                ChatMessageDTO(role=msg['role'], text=msg['text']) 
                for msg in raw_history 
                if msg['role'] != 'system_context'
            ]
            
        return APIResponse(
            status="200",
            result="Succeeded",
            data=ResponseData(items=items)
        )
    except Exception as e:
        # print(f"Error fetching history: {e}")
        return APIResponse(
            status="200", 
            result="Succeeded",
            data=ResponseData(items=[])
        )