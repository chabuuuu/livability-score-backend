from datetime import datetime
import os
import json
import asyncio
from typing import Optional
import jwt
from pydantic import BaseModel
from config.property_db_config import get_property_db
from config.scoring_db_config import get_scoring_db
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from dotenv import load_dotenv
from config.redis_config import redis_client
from schema.common import APIResponse, ResponseData
from itertools import cycle

load_dotenv()
from model.livability_score import PropertyLivabilityScore
from model.property import Property 

# --- CẤU HÌNH ---
KEYS_STR = os.getenv("GEMINI_API_KEYS", "")
if not KEYS_STR:
    # Fallback nếu dùng biến cũ
    single_key = os.getenv("GEMINI_API_KEY")
    API_KEYS = [single_key] if single_key else []
else:
    API_KEYS = [k.strip() for k in KEYS_STR.split(",") if k.strip()]

if not API_KEYS:
    print("❌ CRITICAL WARNING: No GEMINI_API_KEYS found!")

# Tạo vòng lặp vô tận để lấy key lần lượt (Round-Robin)
key_cycle = cycle(API_KEYS)

def get_next_key():
    """Lấy API Key tiếp theo trong danh sách để chia tải."""
    try:
        key = next(key_cycle)
        # print(f"DEBUG: Using API Key ending in ...{key[-4:]}")
        return key
    except StopIteration:
        raise Exception("No API Keys available")

# --- 2. CẤU HÌNH MODEL POOL (Fallback) ---
FALLBACK_MODELS = [
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite", 
    "gemini-robotics-er-1.5-preview"
]


# --- CẤU HÌNH BẢO MẬT JWT ---
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key") # Bắt buộc phải khớp với User Service
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

router = APIRouter(prefix="/api/v1/recommendation/insight", tags=["AI Insight"])
security = HTTPBearer()

CACHE_TTL_DB = 900      # 15 phút
CACHE_TTL_AI = 86400   # 1 ngày 
CACHE_TTL_CHAT_HISTORY = 86400  # 1 ngày

# --- HELPER: Verify Token & Get User ID ---
def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> int:
    """
    Verify Token Signature và trích xuất userId.
    Nếu token giả mạo hoặc hết hạn -> Raise 401 Unauthorized.
    """
    token = credentials.credentials
    
    try:
        # 1. VERIFY SIGNATURE (Quan trọng)
        # decode sẽ tự động check: Signature khớp ko? Token hết hạn (exp) chưa?
        payload = jwt.decode(
            token, 
            key=JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True} # Bắt buộc check hết hạn
        )
        
        # 2. Parse thông tin User (Do cấu trúc đặc thù của payload bạn gửi)
        # Payload mẫu: {"user": "{\"userId\":1, ...}", ...}
        user_str = payload.get("user")
        if not user_str:
            # Token hợp lệ nhưng không có info user -> Có thể coi là lỗi hoặc Anonymous
            raise ValueError("Token missing user claim")
            
        # Parse chuỗi JSON lồng nhau
        if isinstance(user_str, str):
            user_data = json.loads(user_str)
            return user_data.get("userId")
        elif isinstance(user_str, dict):
            return user_str.get("userId")
            
        return 0

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        print(f"JWT Decode Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(f"Auth Parsing Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- HELPER: Lấy Context (Cache Lớp 1) ---
def get_nearby_amenities_with_cache(scoring_db: Session, property_db: Session, property_id: int):
    cache_key = f"rec:insight:context:{property_id}"
    
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        print(f"Redis Read Error: {e}")

    prop_loc_wkt = property_db.query(func.ST_AsText(Property.location)).filter(Property.id == property_id).scalar()
    if not prop_loc_wkt:
        return {}

    sql = text("""
        WITH ranked_amenities AS (
            SELECT 
                category,
                name,
                ST_Distance(location::geography, ST_GeomFromText(:prop_loc, 4326)::geography) as dist_m,
                google_rating,
                ROW_NUMBER() OVER (
                    PARTITION BY category 
                    ORDER BY location <-> ST_GeomFromText(:prop_loc, 4326)
                ) as rn
            FROM amenities
            WHERE category IN ('healthcare', 'education', 'shopping', 'transportation', 'environment', 'entertainment', 'public_safety')
            AND ST_DWithin(location::geography, ST_GeomFromText(:prop_loc, 4326)::geography, 2000)
        )
        SELECT category, name, dist_m, google_rating
        FROM ranked_amenities
        WHERE rn <= 2;
    """)
    
    results = scoring_db.execute(sql, {"prop_loc": prop_loc_wkt}).fetchall()
    
    grouped_data = {cat: [] for cat in ['healthcare', 'education', 'shopping', 'transportation', 'environment', 'entertainment', 'public_safety']}
    for row in results:
        cat = row.category
        if cat in grouped_data:
            grouped_data[cat].append(f"- {row.name} (cách {int(row.dist_m)}m, Rating: {row.google_rating or 'N/A'})")
    
    final_context = {}
    for cat, items in grouped_data.items():
        final_context[cat] = "\n".join(items) if items else "Không tìm thấy trong bán kính 2km"
    
    try:
        redis_client.setex(cache_key, CACHE_TTL_DB, json.dumps(final_context))
    except Exception:
        pass
        
    return final_context

# --- AI GENERATION WITH FALLBACK LOGIC ---
async def generate_content_safe(prompt: str):
    """
    Logic retry thông minh:
    1. Duyệt qua từng Model trong danh sách ưu tiên.
    2. Với mỗi Model, thử tối đa 3 API Key khác nhau.
    3. Nếu gặp Rate Limit (429) -> Đổi Key.
    4. Nếu hết Key mà vẫn lỗi -> Đổi Model.
    """
    last_exception = None
    
    # Duyệt qua các Model (từ Flash -> Pro)
    for model_name in FALLBACK_MODELS:
        print(f"🔄 Trying model: {model_name}")

        # Với mỗi model, thử tối đa 3 lần với 3 key khác nhau (tránh lặp vô tận nếu tất cả key đều chết)
        # Hoặc thử len(API_KEYS) lần nếu muốn vét cạn
        max_retries_per_model = min(len(API_KEYS), 3) 
        
        for attempt in range(max_retries_per_model):
            try:
                # 1. Lấy Key mới (Round-Robin)
                current_key = get_next_key()
                
                # 2. Configure lại GenAI với key này
                # Lưu ý: genai.configure là toàn cục, trong môi trường async concurrency cao có thể bị race condition nhẹ
                # nhưng với tính chất retry của hàm này thì chấp nhận được.
                genai.configure(api_key=current_key)
                
                # 3. Khởi tạo Model
                current_model = genai.GenerativeModel(model_name=model_name)
                
                # 4. Gọi API
                # print(f"DEBUG: Trying {model_name} with key ...{current_key[-4:]} (Attempt {attempt+1})")
                response = await current_model.generate_content_async(prompt, stream=True)
                
                # 5. Yield kết quả (Thành công!)
                async for chunk in response:
                    yield chunk
                return # Thoát hoàn toàn hàm

            except google_exceptions.ResourceExhausted:
                print(f"⚠️ Rate Limit (429) on {model_name}. Rotating key...")
                continue # Thử key tiếp theo
            
            except Exception as e:
                # Các lỗi khác (400, 500) thường do prompt hoặc server sập, đổi key ít khi sửa được
                # Nhưng ta cứ thử đổi model cho chắc
                print(f"❌ Error on {model_name}: {e}. Switching model...")
                last_exception = e
                break # Break vòng lặp Key để chuyển sang Model tiếp theo ngay
    
    # Nếu chạy hết vòng lặp mà không return
    print("❌ SYSTEM OVERLOAD: All keys and models exhausted.")
    raise last_exception if last_exception else Exception("All AI services unavailable.")


# --- API STREAMING ---
@router.get("/analyze/stream/{property_id}")
async def analyze_livability_stream(
    property_id: int,
    user_id: int = Depends(get_current_user_id), # Bây giờ user_id đã được verify an toàn
    scoring_db: Session = Depends(get_scoring_db),
    property_db: Session = Depends(get_property_db)
):
    score_record = scoring_db.query(PropertyLivabilityScore).filter(
        PropertyLivabilityScore.property_id == property_id
    ).first()

    if not score_record:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu điểm sống")

    # Key cache riêng cho user
    ai_cache_key = f"rec:insight:ai_response:{property_id}:{user_id}"
    
    async def generate_stream():
        # 2. Check Cache
        cached_analysis = redis_client.get(ai_cache_key)
        
        if cached_analysis:
            full_text = cached_analysis 
            chunk_size = 50 
            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i:i+chunk_size]
                yield json.dumps({"type": "content", "text": chunk}) + "\n"
                await asyncio.sleep(0.01)
            return

        # 3. Call AI
        nearby_context = get_nearby_amenities_with_cache(scoring_db, property_db, property_id)

        prompt = f"""
        Bạn là một chuyên gia phân tích bất động sản tại Việt Nam. 
        Hãy phân tích và giải thích "Chỉ số đáng sống" (Livability Score) cho một bất động sản dựa trên dữ liệu dưới đây.

        --- DỮ LIỆU ĐIỂM SỐ (Thang 0-100) ---
        - Y tế: {score_record.score_healthcare} (Khoảng cách gần nhất: {score_record.dist_healthcare}m)
        - Giáo dục: {score_record.score_education} (Khoảng cách gần nhất: {score_record.dist_education}m)
        - Mua sắm: {score_record.score_shopping} (Số lượng quán quanh 500m: {score_record.count_shopping})
        - Giao thông: {score_record.score_transportation} (Khoảng cách bến xe/trạm: {score_record.dist_transportation}m)
        - Môi trường/Công viên: {score_record.score_environment} (Khoảng cách: {score_record.dist_environment}m)
        - Giải trí: {score_record.score_entertainment} (Số lượng quán quanh 1km: {score_record.count_entertainment})
        - An ninh: {score_record.score_safety} (Khoảng cách đồn CA: {score_record.dist_safety}m)

        --- CHỈ SỐ ĐẶC BIỆT (Tác động từ tin tức thực tế) ---
        - Ngập lụt (Điểm trừ): {score_record.flood_impact_score or 0} (Nếu cao nghĩa là khu vực này thường xuyên có tin ngập)
        - Tai nạn/An ninh (Điểm trừ): {score_record.accident_impact_score or 0} (Nếu cao nghĩa là có tin về tai nạn hoặc an ninh kém)
        - Tiềm năng phát triển (Điểm cộng): {score_record.future_project_score or 0} (Nếu cao nghĩa là có tin về dự án hạ tầng sắp triển khai)

        --- ĐỊA ĐIỂM THỰC TẾ XUNG QUANH (Context) ---
        Biết rằng xung quanh bất động sản này có các địa điểm nổi bật sau:
        1. Y tế:
        {nearby_context.get('healthcare')}
        2. Giáo dục:
        {nearby_context.get('education')}
        3. Mua sắm:
        {nearby_context.get('shopping')}
        4. Môi trường sống (Công viên):
        {nearby_context.get('environment')}
        5. Giao thông:
        {nearby_context.get('transportation')}

        --- YÊU CẦU ---
        Hãy viết một đoạn nhận xét ngắn gọn (khoảng 150-200 từ) bằng tiếng Việt, giọng văn chuyên nghiệp nhưng gần gũi:
        1. Đánh giá tổng quan: Khu vực này mạnh về điểm gì, yếu về điểm gì?
        2. Phân tích Tác động Đặc biệt: 
           - Nếu có điểm trừ ngập lụt/tai nạn: Hãy cảnh báo khéo léo người mua cần lưu ý.
           - Nếu có điểm cộng tiềm năng: Hãy nhấn mạnh đây là cơ hội đầu tư tốt nhờ hạ tầng tương lai.
        3. Chi tiết đắt giá: Hãy nhắc tên cụ thể các địa điểm (ví dụ: "Lợi thế lớn nhất là nằm ngay sát Bệnh viện X và gần Trường Y...").
        4. Kết luận: Khu vực này phù hợp với ai (Gia đình trẻ, người độc thân, người già...)?
        
        Lưu ý: Bạn hãy vận dụng kiến thức thực tế sẵn có của mình hoặc tìm kiếm trên internet về các địa điểm trên (về quy mô, uy tín, chất lượng chuyên môn...) để đưa ra nhận xét sâu sắc và chính xác, không bịa đặt thông tin.
        """

        print("DEBUG: Prompt prepared, calling AI...")
        print(prompt)

        full_response_buffer = "" 

        try:
            async for chunk in generate_content_safe(prompt):
                if chunk.text:
                    yield json.dumps({"type": "content", "text": chunk.text}) + "\n"
                    full_response_buffer += chunk.text
            
            if full_response_buffer:
                redis_client.setex(ai_cache_key, CACHE_TTL_AI, full_response_buffer)
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(generate_stream(), media_type="application/x-ndjson")


class ChatInsightRequest(BaseModel):
    property_id: int
    message: str
    
# --- API 2: CHAT WITH INSIGHT (NEW) ---
@router.post("/chat/stream")
async def chat_insight_stream(
    payload: ChatInsightRequest,
    user_id: int = Depends(get_current_user_id),
    scoring_db: Session = Depends(get_scoring_db),
    property_db: Session = Depends(get_property_db)
):
    """
    API Chat để hỏi thêm chi tiết dựa trên context đã có trong Redis.
    """
    property_id = payload.property_id
    user_message = payload.message

    # 1. Lấy dữ liệu điểm số mới nhất để đưa vào context chat (quan trọng để AI biết các chỉ số đặc biệt)
    score_record = scoring_db.query(PropertyLivabilityScore).filter(
        PropertyLivabilityScore.property_id == property_id
    ).first()

    # 1. Lấy Context từ Redis (Cache Lớp 1 - Raw Data)
    # Nếu không có trong Redis thì query lại DB
    raw_context = get_nearby_amenities_with_cache(scoring_db, property_db, property_id)
    
    # 2. Lấy Lịch sử phân tích từ Redis (Cache Lớp 2 - Previous Analysis)
    ai_cache_key = f"rec:insight:ai_response:{property_id}:{user_id}"
    previous_analysis = redis_client.get(ai_cache_key)
    
    # Nếu chưa có phân tích trước đó, ta dùng một thông báo mặc định
    if not previous_analysis:
        previous_analysis = "Chưa có bài phân tích chi tiết trước đó."

    # 3. Lấy Lịch sử Chat từ Redis (Chat History)
    chat_history_key = f"rec:insight:chat_history:{property_id}:{user_id}"
    chat_history_data = redis_client.get(chat_history_key)
    chat_history = []
    
    if chat_history_data:
        try:
            chat_history = json.loads(chat_history_data)
        except Exception:
            chat_history = []
    
    # Chỉ lấy 6 tin nhắn gần nhất (3 cặp hỏi-đáp) để đưa vào context
    recent_history = chat_history[-6:]
    history_str = ""
    for msg in recent_history:
        role = "Khách hàng" if msg['role'] == 'user' else "AI"
        history_str += f"- {role}: {msg['text']}\n"

    # 4. Xây dựng Prompt hội thoại
    chat_prompt = f"""
    Bạn là một trợ lý AI chuyên về bất động sản. Bạn đang hỗ trợ khách hàng #{user_id} tìm hiểu về một căn nhà.
    
    --- CHỈ SỐ ĐẶC BIỆT CỦA CĂN NHÀ ---
    - Điểm trừ Ngập lụt: {score_record.flood_impact_score if score_record else 0}
    - Điểm trừ Tai nạn: {score_record.accident_impact_score if score_record else 0}
    - Điểm cộng Tiềm năng: {score_record.future_project_score if score_record else 0}

    --- DỮ LIỆU THỰC TẾ (Context) ---
    Đây là các tiện ích xung quanh căn nhà (đã được xác thực):
    - Y tế: {raw_context.get('healthcare', 'Không rõ')}
    - Giáo dục: {raw_context.get('education', 'Không rõ')}
    - Mua sắm: {raw_context.get('shopping', 'Không rõ')}
    - Môi trường: {raw_context.get('environment', 'Không rõ')}
    - Giao thông: {raw_context.get('transportation', 'Không rõ')}

    --- LỊCH SỬ PHÂN TÍCH TRƯỚC ĐÓ ---
    "{previous_analysis}"

    --- LỊCH SỬ HỘI THOẠI ---
    {history_str}

    --- CÂU HỎI MỚI ---
    Khách hàng: "{user_message}"

    --- YÊU CẦU ---
    Hãy trả lời câu hỏi của khách hàng một cách ngắn gọn, súc tích và hữu ích. 
    Nếu khách hàng hỏi về thông tin có trong Context, hãy dùng nó để trả lời chính xác.
    Nếu khách hàng hỏi về ngập lụt, tai nạn hay quy hoạch, hãy dựa vào các "Chỉ số đặc biệt" ở trên để trả lời (ví dụ điểm ngập cao thì cảnh báo).
    Nếu câu hỏi nằm ngoài Context (ví dụ: phong thủy, giá đất tương lai), hãy trả lời dựa trên kiến thức chung của bạn nhưng cần lưu ý là tham khảo.
    """

    async def generate_chat_stream():
        full_response = ""
        try:
            # FIX: Sử dụng hàm wrapper an toàn
            async for chunk in generate_content_safe(chat_prompt):
                if chunk.text:
                    yield json.dumps({"type": "content", "text": chunk.text}) + "\n"
                    full_response += chunk.text
            
            # Sau khi stream xong, lưu lại lịch sử vào Redis
            if full_response:
                # Append tin nhắn mới
                chat_history.append({"role": "user", "text": user_message, "created_at": datetime.now().isoformat()})
                chat_history.append({"role": "model", "text": full_response, "created_at": datetime.now().isoformat()})

                # Giữ lại tối đa 20 tin nhắn trong bộ nhớ Redis để không bị tràn
                updated_history = chat_history[-20:]
                redis_client.setex(chat_history_key, CACHE_TTL_CHAT_HISTORY, json.dumps(updated_history))

        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(generate_chat_stream(), media_type="application/x-ndjson")


class ChatMessageDTO(BaseModel):
    role: str
    text: str
    created_at: Optional[datetime] = None

@router.get("/chat/history/{property_id}", response_model=APIResponse[ChatMessageDTO])
async def get_chat_history(
    property_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """
    Lấy toàn bộ lịch sử chat của user với BĐS này từ Redis.
    """
    try:
        chat_history_key = f"rec:insight:chat_history:{property_id}:{user_id}"
        chat_history_data = redis_client.get(chat_history_key)
        
        items = []
        if chat_history_data:
            items = json.loads(chat_history_data)
            
        return APIResponse(
            status="200",
            result="Succeeded",
            data=ResponseData(items=items)
        )
    except Exception as e:
        print(f"Error fetching history: {e}")
        return APIResponse(
            status="200", # Trả về rỗng thay vì lỗi 500 nếu Redis lỗi nhẹ
            result="Succeeded",
            data=ResponseData(items=[])
        )