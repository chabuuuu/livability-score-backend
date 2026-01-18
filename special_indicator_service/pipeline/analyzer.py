import json
import math
import google.generativeai as genai
from sqlalchemy import text

from config.config import generate_content_smart
from config.property_db_config import PropertySession
from config.scoring_db_config import ScoringSession
from sqlalchemy import text
from geoalchemy2 import Geometry 
# Số lượng bài báo trong 1 request
BATCH_SIZE = 10 

# --- FORMULA ---

def calculate_flood_score(depth_cm, duration_h, location_scope):
    """
    Tính điểm ngập lụt (Negative).
    S = min(10, (D/Dmax * wd) + (T/Tmax * wt) + alpha)
    """
    D_max = 50.0  # cm
    T_max = 4.0   # giờ
    w_d = 6.0
    w_t = 3.0
    
    # scope: 1 (Hẻm/Cục bộ), 2 (Đường chính), 3 (Diện rộng) -> map sang alpha
    # Input scope từ AI có thể là int 1, 2, 3
    alpha = 0
    if location_scope == 2: alpha = 1.0
    elif location_scope == 3: alpha = 2.0
    
    # Tính toán
    term_d = (min(depth_cm, D_max * 1.5) / D_max) * w_d # Cap depth để không quá lớn
    term_t = (min(duration_h, T_max * 1.5) / T_max) * w_t
    
    score = term_d + term_t + alpha
    return min(10.0, score)

def calculate_accident_score(fatalities, injuries, vehicles):
    """
    Tính điểm tai nạn (Negative).
    S = min(10, 5*dead + 1.5*injured + 0.5*vehicles)
    """
    w_f = 5.0
    w_i = 1.5
    w_v = 0.5
    
    score = (w_f * fatalities) + (w_i * injuries) + (w_v * vehicles)
    return min(10.0, score)

def calculate_project_score(capital_billion, status_str, type_str):
    """
    Tính điểm tiềm năng dự án (Positive).
    S = min(10, log10(C + 10) * K_status * K_type)
    """
    # Mapping hệ số
    K_status = 0.3 # Default PROPOSAL
    if status_str == 'APPROVED': K_status = 0.5
    elif status_str == 'ONGOING': K_status = 0.8
    elif status_str == 'NEAR_FINISH': K_status = 1.0
    
    K_type = 0.5 # Default OTHER
    if type_str == 'METRO': K_type = 1.5
    elif type_str == 'BRIDGE_ROAD': K_type = 1.2
    elif type_str == 'EXPANSION': K_type = 0.8
    
    # Công thức
    # Thêm 10 vào capital để tránh log số nhỏ/âm và tạo nền
    # log10(100 tỷ) = 2, log10(1000 tỷ) = 3, log10(10000 tỷ) = 4
    base_val = math.log10(max(1, capital_billion) + 10)
    
    score = base_val * K_status * K_type
    
    # Scale lên một chút vì log10 thường nhỏ (VD: log10(5000) ~ 3.7)
    # Nếu muốn max 10 thì cần nhân thêm hệ số hoặc để nguyên nếu muốn điểm dự án khó đạt 10
    # Với công thức hiện tại: 5000 tỷ, Ongoing, Cầu lớn => 3.7 * 0.8 * 1.2 = 3.55 (Hợp lý cho điểm cộng thêm)
    
    return min(10.0, score)

# --- 2. LOGIC CHÍNH ---

def analyze_and_map_news():
    print(f"--- [Analyzer] Bắt đầu phân tích tin tức (Batch Size: {BATCH_SIZE}) ---")
    score_db = ScoringSession()
    
    # Lấy danh sách bài báo chưa phân tích
    sql_get = text("""
        SELECT n.id, n.title, n.content, d.district_name 
        FROM news_articles n
        JOIN district_special_stats d ON n.district_id = d.id
        WHERE n.topic IS NULL 
        ORDER BY n.id DESC LIMIT 300
    """)
    articles = score_db.execute(sql_get).fetchall()
    
    if not articles:
        print("    -> Không có bài báo mới cần phân tích.")
        score_db.close()
        return

    # Chia batch
    article_batches = [articles[i:i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)]
    
    for batch in article_batches:
        try:
            process_batch(batch, score_db)
        except Exception as e:
            print(f"    !!! Critical Error processing batch: {e}")

    # Trigger Update
    aggregate_and_propagate_scores(score_db)
    score_db.close()

def process_batch(batch, db):
    """Gửi batch tới Gemini để trích xuất số liệu, sau đó tính điểm bằng Python"""
    
    articles_text = ""
    for art in batch:
        content_snippet = art.content[:1000].replace("\n", " ") 
        articles_text += f"""
        --- ID: {art.id} ---
        Quận: "{art.district_name}"
        Tiêu đề: "{art.title}"
        Nội dung: "{content_snippet}..."
        --------------------
        """

    # Batch Prompt - Yêu cầu trích xuất số liệu
    prompt = f"""
    Bạn là một chuyên gia Kỹ thuật Dữ liệu Đô thị (Urban Data Engineer). Nhiệm vụ của bạn là trích xuất và chuẩn hóa thông tin từ các bản tin bất động sản/đô thị thành dữ liệu có cấu trúc.

    DỮ LIỆU ĐẦU VÀO:
    {articles_text}

    --- QUY TẮC CHUYỂN ĐỔI (QUAN TRỌNG) ---
    Khi gặp thông tin định tính, hãy quy đổi sang số theo bảng sau:

    1. NGẬP LỤT (FLOOD) - depth_cm & duration_h:
       - "Ngập mắt cá chân/xâm xấp": 15 cm
       - "Ngập nửa bánh xe": 25 cm
       - "Ngập lút bánh xe/chết máy": 40 cm
       - "Ngập yên xe/tràn vào nhà": 60 cm
       - "Ùn ứ/Di chuyển chậm": duration = 1.0h
       - "Kẹt xe nghiêm trọng/Tê liệt": duration = 3.0h
       - Nếu không rõ thời gian, mặc định duration = 2.0h

    2. DỰ ÁN (PROJECT) - status:
       - "Đề xuất", "Chủ trương", "Ý tưởng": -> "PROPOSAL"
       - "Đã duyệt", "Quy hoạch 1/500", "Bàn giao mặt bằng": -> "APPROVED"
       - "Khởi công", "Đang xây dựng", "Tiến độ": -> "ONGOING"
       - "Hợp long", "Thông xe", "Sắp khánh thành": -> "NEAR_FINISH"
       - Loại hình (type): Metro/Đường sắt (METRO), Cầu/Đường lớn/Cao tốc (BRIDGE_ROAD), Mở rộng hẻm/Nâng cấp đường (EXPANSION).

    3. TAI NẠN (ACCIDENT):
       - Nếu bài viết chỉ nói "thương vong" chung chung: Giả định 1 injuries.
       - "Nghiêm trọng" nhưng không nêu số người: Giả định 1 injuries, 2 vehicles.

    --- YÊU CẦU XỬ LÝ VỚI TỪNG BÀI BÁO ---
    1. VALIDATE: Kiểm tra xem sự kiện có thực sự ảnh hưởng đến "Quận" được ghi trong input không. (Ví dụ: Bài báo nói về Q.7 nhưng input là Q.1 -> is_relevant = false).
    2. CLASSIFY: Chỉ chọn 1 Topic chính xác nhất. Ưu tiên theo thứ tự: FLOOD > ACCIDENT > PROJECT > OTHER.
    3. EXTRACT: Trích xuất số liệu. Nếu thiếu số liệu, hãy dùng logic suy luận hợp lý nhất từ ngữ cảnh hoặc dùng giá trị mặc định an toàn.

    --- OUTPUT FORMAT ---
    Trả về duy nhất một JSON List (Array of Objects). Không thêm markdown code block (```json). Không thêm giải thích.

    Cấu trúc mỗi object:
    {{
        "id": int,                 // Giữ nguyên ID đầu vào
        "is_relevant": bool,       // True nếu bài báo đúng quận
        "reason": string,          // Lý do ngắn gọn nếu false hoặc lý do chọn topic
        "topic": "FLOOD" | "ACCIDENT" | "PROJECT" | "OTHER",
        "summary": string,         // Tóm tắt sự kiện dưới 20 từ
        
        // Chỉ null nếu topic khác FLOOD
        "flood_data": {{
            "depth_cm": int,       // Mặc định 0
            "duration_h": float,   // Mặc định 1.0
            "scope": int           // 1: Hẻm/Cục bộ, 2: Đường chính/Liên phường, 3: Diện rộng/Toàn quận
        }},
        
        // Chỉ null nếu topic khác ACCIDENT
        "accident_data": {{
            "fatalities": int,     // Số người chết, mặc định 0
            "injuries": int,       // Số người bị thương, mặc định 0
            "vehicles": int        // Số xe hư hỏng, mặc định 1
        }},
        
        // Chỉ null nếu topic khác PROJECT
        "project_data": {{
            "capital_billion": float, // Vốn đầu tư (tỷ VNĐ). Nếu USD hãy đổi sang VND (tỷ giá 25000). Mặc định 10.0
            "status": "PROPOSAL" | "APPROVED" | "ONGOING" | "NEAR_FINISH",
            "type": "METRO" | "BRIDGE_ROAD" | "EXPANSION" | "OTHER"
        }}
    }}
    """

    print("    -> Gửi yêu cầu trích xuất tới Gemini...")
    
    try:
        # Gọi Gemini
        response = generate_content_smart(prompt)
        # Clean response text (đôi khi Gemini trả về markdown ```json ... ```)
        text_resp = response.text.replace("```json", "").replace("```", "").strip()
        
        results = json.loads(text_resp)
        
        # Duyệt kết quả và tính điểm
        for item in results:
            art_id = item.get('id')
            topic = item.get('topic')
            is_relevant = item.get('is_relevant', False)
            
            # Tìm bài báo gốc để log
            original_art = next((a for a in batch if a.id == art_id), None)
            dist_name = original_art.district_name if original_art else "Unknown"

            if not is_relevant or topic == 'OTHER':
                # Xóa hoặc mark ignore
                if not is_relevant:
                    print(f"    -> [DELETE] Art {art_id} ({dist_name}): {item.get('reason')}")
                    db.execute(text("DELETE FROM news_articles WHERE id = :id"), {"id": art_id})
                else:
                    # Topic OTHER -> Set topic nhưng score = 0
                    db.execute(text("UPDATE news_articles SET topic='OTHER', impact_score=0 WHERE id=:id"), {"id": art_id})
            else:
                # --- TÍNH ĐIỂM DỰA TRÊN SỐ LIỆU ---
                final_score = 0.0
                
                if topic == 'FLOOD':
                    data = item.get('flood_data', {})
                    final_score = calculate_flood_score(
                        data.get('depth_cm', 0),
                        data.get('duration_h', 1.0),
                        data.get('scope', 1)
                    )
                elif topic == 'ACCIDENT':
                    data = item.get('accident_data', {})
                    final_score = calculate_accident_score(
                        data.get('fatalities', 0),
                        data.get('injuries', 0),
                        data.get('vehicles', 1)
                    )
                elif topic == 'PROJECT':
                    data = item.get('project_data', {})
                    final_score = calculate_project_score(
                        data.get('capital_billion', 10.0),
                        data.get('status', 'PROPOSAL'),
                        data.get('type', 'OTHER')
                    )

                # Update Database
                update_sql = text("""
                    UPDATE news_articles 
                    SET topic = :topic, 
                        impact_score = :score, 
                        sentiment = :sentiment, 
                        summary = :summary,
                        fetched_at = NOW()
                    WHERE id = :aid
                """)
                
                # Sentiment logic đơn giản dựa trên topic
                sentiment = 'POSITIVE' if topic == 'PROJECT' else 'NEGATIVE'
                
                db.execute(update_sql, {
                    "topic": topic, 
                    "score": round(final_score, 2), 
                    "sentiment": sentiment, 
                    "summary": item.get('summary', ''), 
                    "aid": art_id
                })
                
                print(f"    -> [UPDATE] Art {art_id} ({dist_name}): {topic} | Score: {final_score:.2f}")
        
        db.commit()

    except json.JSONDecodeError:
        print("    ! Error: AI response is not valid JSON.")
        print(text_resp[:500]) # Debug log
    except Exception as e:
        print(f"    ! Error processing batch: {e}")

# Hàm này giữ nguyên logic tổng hợp từ các điểm số đã tính
def aggregate_and_propagate_scores(score_db):
    print("--- [Aggregator] Tổng hợp điểm và Update Cross-DB ---")
    
    # 1. Tổng hợp điểm vào District Stats
    # Áp dụng mô hình Tích lũy Logarit Tổng quát (Generalized Logarithmic Accumulation)
    # Tất cả các chỉ số đều được chuẩn hóa về thang điểm [0, 10]
    
    agg_sql = text("""
        UPDATE district_special_stats d
        SET 
            -- 1. NGẬP LỤT (FLOOD)
            -- Cấu hình: Cmax=10, K=4.2 (Độ nhạy cao), Lambda=0.05 (Suy giảm sau 2 tuần)
            flood_impact_score = LEAST(10, 
                4.2 * LN(1 + (
                    SELECT COALESCE(SUM(
                        impact_score * EXP(-0.05 * EXTRACT(DAY FROM (NOW() - published_date)))
                    ), 0) 
                    FROM news_articles 
                    WHERE district_id = d.id 
                    AND topic = 'FLOOD' 
                    AND published_date > NOW() - INTERVAL '60 days'
                ))
            ),
            
            -- 2. TAI NẠN (ACCIDENT)
            -- Cấu hình: Cmax=10, K=3.0 (Độ nhạy trung bình - Cần tích lũy), Lambda=0.05
            accident_impact_score = LEAST(10, 
                3.0 * LN(1 + (
                    SELECT COALESCE(SUM(
                        impact_score * EXP(-0.05 * EXTRACT(DAY FROM (NOW() - published_date)))
                    ), 0) 
                    FROM news_articles 
                    WHERE district_id = d.id 
                    AND topic = 'ACCIDENT' 
                    AND published_date > NOW() - INTERVAL '60 days'
                ))
            ),
            
            -- 3. DỰ ÁN (PROJECT)
            -- Cấu hình: Cmax=10, K=4.2 (Độ nhạy cao), Lambda=0 (KHÔNG SUY GIẢM)
            -- Lý do: Thông tin quy hoạch có giá trị tích lũy dài hạn, không mất đi theo ngày.
            future_project_score = LEAST(10, 
                4.2 * LN(1 + (
                    SELECT COALESCE(SUM(impact_score), 0) 
                    FROM news_articles 
                    WHERE district_id = d.id 
                    AND topic = 'PROJECT' 
                    AND published_date > NOW() - INTERVAL '365 days' -- Window dài hạn 1 năm
                ))
            ),
            
            last_analyzed_at = NOW()
    """)
    
    try:
        score_db.execute(agg_sql)
        score_db.commit()
        print("    -> [Success] Đã tính toán xong chỉ số cấp Quận (Max 10).")
    except Exception as e:
        score_db.rollback()
        print(f"    -> [Error] Lỗi khi tổng hợp District Stats: {e}")
        return

    # 2. Lan truyền Cross-DB (Propagate to Properties)
    # Logic: Lấy điểm từ bảng District (Scoring DB) -> Tìm BĐS thuộc quận đó (Property DB) -> Update điểm cho BĐS (Scoring DB)
    
    # Lấy danh sách quận đã có điểm
    districts = score_db.execute(text("""
        SELECT id, district_name, ST_AsText(boundary) as wkt, 
               flood_impact_score, accident_impact_score, future_project_score
        FROM district_special_stats
        WHERE boundary IS NOT NULL
    """)).fetchall()
    
    prop_db = PropertySession() # Session kết nối tới DB chứa Bất động sản
    total_props_updated = 0
    
    for dist in districts:
        if not dist.wkt: continue
        
        try:
            # Tìm ID các BĐS nằm trong quận này (Spatial Query trên Property DB)
            find_props_sql = text("SELECT id FROM properties WHERE ST_Within(location::geometry, ST_GeomFromText(:wkt, 4326))")
            prop_ids = [row.id for row in prop_db.execute(find_props_sql, {"wkt": dist.wkt}).fetchall()]
            
            if not prop_ids: continue
                
            # Batch Update vào bảng điểm (Scoring DB)
            # Lưu ý: P_flood, P_accident, P_project lúc này đều Max = 10
            batch_size = 1000
            for i in range(0, len(prop_ids), batch_size):
                batch_ids = tuple(prop_ids[i:i + batch_size])
                
                # Cần xử lý tuple trong SQL (với tuple 1 phần tử python thêm dấu phẩy gây lỗi syntax nếu không xử lý kỹ)
                # Dùng list expanding parameter là an toàn nhất với SQLAlchemy
                update_score_sql = text("""
                    UPDATE property_livability_scores
                    SET flood_impact_score = :flood, 
                        accident_impact_score = :accident, 
                        future_project_score = :project
                    WHERE property_id IN :ids
                """)
                
                score_db.execute(update_score_sql, {
                    "flood": dist.flood_impact_score, 
                    "accident": dist.accident_impact_score, 
                    "project": dist.future_project_score, 
                    "ids": batch_ids
                })
                score_db.commit()
                
            total_props_updated += len(prop_ids)
            print(f"    -> Quận {dist.district_name}: Synced {len(prop_ids)} properties.")
            
        except Exception as e:
            print(f"    -> [Error] Lỗi xử lý quận {dist.district_name}: {e}")
            score_db.rollback()

    prop_db.close()
    print(f"--- [Aggregator] Hoàn tất. Tổng cộng cập nhật {total_props_updated} bất động sản. ---")