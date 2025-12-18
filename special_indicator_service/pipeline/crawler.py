import time
from ddgs import DDGS
from newspaper import Article
from sqlalchemy import text
from config.config import KEYWORDS, OSM_DISTRICT_QUERIES
from config.scoring_db_config import ScoringSession

def crawl_news():
    print("--- [Crawler] Bắt đầu thu thập tin tức (DuckDuckGo) ---")
    db = ScoringSession()
    ddgs = DDGS()
    total_new = 0
    
    # Lấy danh sách tên quận ngắn gọn
    search_districts = [d.split(',')[0] for d in OSM_DISTRICT_QUERIES]
    
    for district_name in search_districts:
        # 1. Lấy district_id tương ứng trong DB
        dist_row = db.execute(
            text("SELECT id FROM district_special_stats WHERE district_name = :name"),
            {"name": district_name}
        ).fetchone()
        
        if not dist_row:
            print(f"    ! Warning: Không tìm thấy ID cho quận '{district_name}' trong DB. Bỏ qua.")
            continue
            
        district_id = dist_row[0]

        for topic_key, keys in KEYWORDS.items():
            for key in keys:
                # Query tìm kiếm cụ thể cho quận đó
                query = f"{key} tại {district_name} TP HCM tin mới"
                print(f"    -> Searching: {query} (District ID: {district_id})")
                
                try:
                    # Tìm kiếm tin tức
                    results = ddgs.text(query, region='vn-vn', timelimit='m', max_results=1)
                    
                    for r in results:
                        url = r['href']
                        title = r['title']
                        
                        # Check trùng URL
                        exists = db.execute(text("SELECT 1 FROM news_articles WHERE url = :url"), {"url": url}).fetchone()
                        if exists: continue
                            
                        try:
                            # Tải nội dung
                            article = Article(url)
                            article.download()
                            article.parse()
                            content = article.text[:3000] # Lấy 3000 ký tự đầu
                            
                            # Insert vào DB KÈM THEO district_id
                            sql = text("""
                                INSERT INTO news_articles (title, url, content, district_id, published_date)
                                VALUES (:title, :url, :content, :did, NOW())
                            """)
                            db.execute(sql, {
                                "title": title, 
                                "url": url, 
                                "content": content,
                                "did": district_id # <-- Gán ID ngay tại đây
                            })
                            db.commit()
                            total_new += 1
                            print(f"       + Saved: {title[:30]}... (DistID: {district_id})")
                        except Exception as e:
                            # print(f"       ! Parse Error: {e}")
                            pass
                    
                    time.sleep(2) # Sleep để tránh bị chặn IP
                    
                except Exception as e:
                    print(f"    ! Search Error: {e}")
                    time.sleep(5) # Nghỉ lâu hơn nếu lỗi network
                    
    db.close()
    print(f"--- [Crawler] Hoàn tất. Đã thêm {total_new} bài báo mới. ---")
    return total_new