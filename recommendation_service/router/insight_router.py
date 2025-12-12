import os
from config.property_db_config import get_property_db
from config.scoring_db_config import get_scoring_db
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func, cast
from geoalchemy2 import Geography, Geometry
from dotenv import load_dotenv

load_dotenv()
from model.livability_score import PropertyLivabilityScore
from model.property import Property # Cần model này để lấy tọa độ BĐS
from schema.common import APIResponse

# --- CẤU HÌNH GEMINI ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# Cấu hình Model với Google Search Tool
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Khởi tạo model
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
    # Kích hoạt Google Search để AI lấy thông tin thực tế mới nhất
    tools='google_search_retrieval' 
)

router = APIRouter(prefix="/api/v1/recommendation/insight", tags=["AI Insight"])

# --- HELPER: Lấy danh sách tiện ích cụ thể gần nhất ---
def get_nearby_amenities_context(scoring_db: Session, property_db: Session, property_id: int):
    """
    Truy vấn PostGIS để lấy tên các địa điểm thực tế xung quanh BĐS.
    Giúp AI biết chính xác BĐS nằm cạnh 'Vincom' hay 'Chợ Bà Chiểu'.
    """
    # 1. Lấy tọa độ BĐS
    prop_loc = property_db.query(Property.location).filter(Property.id == property_id).scalar()
    if not prop_loc:
        return {}

    categories = ['healthcare', 'education', 'shopping', 'transportation', 'environment', 'entertainment', 'public_safety']
    context_data = {}

    for cat in categories:
        # Query: Tìm 2 địa điểm gần nhất thuộc category này trong bán kính 2km
        # Sử dụng toán tử <-> (Nearest Neighbor) của PostGIS cực nhanh
        sql = text("""
            SELECT name, 
                   ST_Distance(location::geography, :prop_loc::geography) as dist_m,
                   google_rating
            FROM amenities
            WHERE category = :cat
            AND ST_DWithin(location::geography, :prop_loc::geography, 2000)
            ORDER BY location <-> :prop_loc
            LIMIT 2
        """)
        
        results = scoring_db.execute(sql, {"prop_loc": prop_loc, "cat": cat}).fetchall()
        
        items = []
        for row in results:
            items.append(f"- {row.name} (cách {int(row.dist_m)}m, Rating: {row.google_rating or 'N/A'})")
        
        context_data[cat] = "\n".join(items) if items else "Không tìm thấy trong bán kính 2km"
    
    return context_data

@router.get("/analyze/{property_id}")
async def analyze_livability(
    property_id: int,
    scoring_db: Session = Depends(get_scoring_db),
    property_db: Session = Depends(get_property_db)
):
    """
    Dùng Gemini 2.5 Flash để phân tích và giải thích Livability Score.
    """
    # 1. Lấy điểm số từ DB
    score_record = scoring_db.query(PropertyLivabilityScore).filter(
        PropertyLivabilityScore.property_id == property_id
    ).first()

    if not score_record:
        raise HTTPException(status_code=404, detail="Chưa có dữ liệu điểm sống cho BĐS này")

    # 2. Lấy Context các địa điểm thực tế xung quanh
    nearby_context = get_nearby_amenities_context(scoring_db, property_db, property_id)

    # 3. Xây dựng Prompt cho AI
    # Prompt này kết hợp số liệu thô và tên địa điểm thực tế
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
    2. Chi tiết đắt giá: Hãy nhắc tên cụ thể các địa điểm (ví dụ: "Lợi thế lớn nhất là nằm ngay sát Bệnh viện X và gần Trường Y...").
    3. Kết luận: Khu vực này phù hợp với ai (Gia đình trẻ, người độc thân, người già...)?
    
    Lưu ý: Sử dụng Internet để kiểm tra thêm thông tin về danh tiếng của các địa điểm trên (ví dụ: bệnh viện đó có tốt không) để đưa ra nhận xét chính xác hơn.
    """

    try:
        # 4. Gọi Gemini API
        response = model.generate_content(prompt)
        ai_analysis = response.text

        return APIResponse(
            status="200",
            result="Succeeded",
            data={
                "property_id": property_id,
                "analysis": ai_analysis,
                "scores": {
                    "healthcare": float(score_record.score_healthcare or 0),
                    "education": float(score_record.score_education or 0),
                    "shopping": float(score_record.score_shopping or 0),
                    "environment": float(score_record.score_environment or 0)
                }
            }
        )

    except Exception as e:
        print(f"Gemini Error: {e}")
        return APIResponse(
            status="500",
            result="Failed",
            error="Không thể tạo phân tích AI lúc này."
        )