import json
import google.generativeai as genai
from sqlalchemy import text

from config.config import generate_content_smart
from config.property_db_config import PropertySession
from config.scoring_db_config import ScoringSession

# Số lượng bài báo trong 1 request (Tùy chỉnh dựa trên độ dài trung bình bài báo)
BATCH_SIZE = 13 

def analyze_and_map_news():
    print(f"--- [Analyzer] Bắt đầu phân tích tin tức (Batch Size: {BATCH_SIZE}) ---")
    score_db = ScoringSession()
    
    # 1. Lấy danh sách bài báo chưa phân tích KÈM thông tin Quận
    # Lấy nhiều hơn (ví dụ 100 bài) để tối ưu batch
    sql_get = text("""
        SELECT n.id, n.title, n.content, d.district_name 
        FROM news_articles n
        JOIN district_special_stats d ON n.district_id = d.id
        WHERE n.topic IS NULL 
        ORDER BY n.id DESC LIMIT 100
    """)
    articles = score_db.execute(sql_get).fetchall()
    
    if not articles:
        print("    -> Không có bài báo mới cần phân tích.")
        score_db.close()
        return

    # 2. Chia nhỏ thành các batch
    article_batches = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    
    for batch in article_batches:
        try:
            process_batch(batch, score_db)
        except Exception as e:
            print(f"    !!! Critical Error processing batch: {e}")

    # 3. Trigger Update điểm vùng
    aggregate_and_propagate_scores(score_db)
    score_db.close()

def process_batch(batch, db):
    """Xử lý một nhóm bài báo trong 1 request gửi tới Gemini"""
    
    # Chuẩn bị nội dung cho Prompt
    articles_text = ""
    for art in batch:
        # Cắt ngắn nội dung mỗi bài để tiết kiệm token đầu vào (khoảng 800 ký tự là đủ để AI hiểu)
        content_snippet = art.content[:800].replace("\n", " ") 
        articles_text += f"""
        --- ARTICLE ID: {art.id} ---
        Quận mục tiêu: "{art.district_name}"
        Tiêu đề: "{art.title}"
        Nội dung: "{content_snippet}..."
        -----------------------------
        """

    # Config AI
    # Batch Prompt
    prompt = f"""
    Bạn là chuyên gia phân tích dữ liệu đô thị. Dưới đây là danh sách các bài báo cần xử lý.
    
    {articles_text}

    --- YÊU CẦU ---
    Với MỖI bài báo (dựa theo ARTICLE ID), hãy thực hiện:
    1. Kiểm tra (Validate): Nội dung bài báo có thực sự nói về sự kiện xảy ra tại "Quận mục tiêu" không?
    2. Phân tích: Nếu đúng quận, hãy xác định chủ đề và mức độ ảnh hưởng.

    Hãy trả về kết quả dưới dạng một JSON LIST (Array of Objects). Tuyệt đối không thêm text thừa.
    Cấu trúc mỗi object:
    {{
        "id": (Số nguyên, giữ nguyên ID của bài báo),
        "is_relevant": true/false (Sai quận hoặc tin rác thì false),
        "reason": "Lý do nếu false",
        "topic": "FLOOD" | "ACCIDENT" | "PROJECT" | "OTHER",
        "sentiment": "NEGATIVE" | "POSITIVE",
        "impact_score": (Số nguyên 1-10),
        "summary": "Tóm tắt tiếng Việt cực ngắn (dưới 20 từ)"
    }}
    """

    print("    -> Gửi yêu cầu phân tích batch tới Gemini...")
    print(prompt)

    try:
        # Gọi Gemini
        response = generate_content_smart(prompt)
        text_resp = response.text.replace("```json", "").replace("```", "").strip()

        print("    -> Nhận được phản hồi từ Gemini, xử lý kết quả...")
        print(text_resp)
        
        # Parse JSON Array
        results = json.loads(text_resp)


        
        # Duyệt qua kết quả và update DB
        for item in results:
            art_id = item.get('id')
            is_relevant = item.get('is_relevant', False)
            
            # Tìm bài báo gốc trong batch để log tên quận (Optional)
            original_art = next((a for a in batch if a.id == art_id), None)
            dist_name = original_art.district_name if original_art else "Unknown"

            if not is_relevant:
                # Xóa bài báo không hợp lệ
                print(f"    -> [BATCH DELETE] Art {art_id} ({dist_name}): {item.get('reason')}")
                db.execute(text("DELETE FROM news_articles WHERE id = :id"), {"id": art_id})
            else:
                # Cập nhật kết quả phân tích
                update_sql = text("""
                    UPDATE news_articles 
                    SET topic = :topic, 
                        impact_score = :score, 
                        sentiment = :sentiment, 
                        summary = :summary,
                        fetched_at = NOW()
                    WHERE id = :aid
                """)
                db.execute(update_sql, {
                    "topic": item.get('topic', 'OTHER'), 
                    "score": item.get('impact_score', 0), 
                    "sentiment": item.get('sentiment', 'NEUTRAL'), 
                    "summary": item.get('summary', ''), 
                    "aid": art_id
                })
                print(f"    -> [BATCH UPDATE] Art {art_id} ({dist_name}): {item.get('topic')} - Score {item.get('impact_score')}")
        
        db.commit()

    except json.JSONDecodeError:
        print("    ! Error: AI response is not valid JSON. Skipping batch.")
        # print(text_resp) # Debug
    except Exception as e:
        print(f"    ! Error calling Gemini for batch: {e}")

# Hàm aggregate_and_propagate_scores GIỮ NGUYÊN (không thay đổi logic)
def aggregate_and_propagate_scores(score_db):
    print("--- [Aggregator] Tổng hợp điểm và Update Cross-DB ---")
    
    # 1. Tổng hợp điểm vào District Stats
    agg_sql = text("""
        UPDATE district_special_stats d
        SET 
            flood_impact_score = LEAST((SELECT COALESCE(SUM(impact_score), 0) FROM news_articles WHERE district_id = d.id AND topic = 'FLOOD' AND published_date > NOW() - INTERVAL '30 days') * 0.5, 20),
            accident_impact_score = LEAST((SELECT COALESCE(SUM(impact_score), 0) FROM news_articles WHERE district_id = d.id AND topic = 'ACCIDENT' AND published_date > NOW() - INTERVAL '30 days') * 0.3, 15),
            future_project_score = LEAST((SELECT COALESCE(SUM(impact_score), 0) FROM news_articles WHERE district_id = d.id AND topic = 'PROJECT' AND sentiment = 'POSITIVE') * 0.05, 10),
            last_analyzed_at = NOW()
    """)
    score_db.execute(agg_sql)
    score_db.commit()
    
    # 2. Lan truyền Cross-DB (Logic cũ import PropertySession ở đây)    
    # Lấy danh sách quận có boundary
    districts = score_db.execute(text("""
        SELECT id, district_name, ST_AsText(boundary) as wkt, 
               flood_impact_score, accident_impact_score, future_project_score
        FROM district_special_stats
        WHERE boundary IS NOT NULL
    """)).fetchall()
    
    prop_db = PropertySession()
    total_props_updated = 0
    
    for dist in districts:
        if not dist.wkt: continue
        
        # Tìm BĐS trong quận
        find_props_sql = text("SELECT id FROM properties WHERE ST_Within(location::geometry, ST_GeomFromText(:wkt, 4326))")
        prop_ids = [row.id for row in prop_db.execute(find_props_sql, {"wkt": dist.wkt}).fetchall()]
        
        if not prop_ids: continue
            
        # Batch Update
        batch_size = 1000
        for i in range(0, len(prop_ids), batch_size):
            batch_ids = tuple(prop_ids[i:i + batch_size])
            update_score_sql = text("""
                UPDATE property_livability_scores
                SET flood_impact_score = :flood, accident_impact_score = :accident, future_project_score = :project
                WHERE property_id IN :ids
            """)
            score_db.execute(update_score_sql, {
                "flood": dist.flood_impact_score, "accident": dist.accident_impact_score, 
                "project": dist.future_project_score, "ids": batch_ids
            })
            score_db.commit()
            
        total_props_updated += len(prop_ids)
        print(f"    -> Quận {dist.district_name}: Synced {len(prop_ids)} properties.")

    prop_db.close()