import schedule
import time
import os
from config.scoring_db_config import ScoringSession
from initializer import init_district_boundaries
from pipeline.crawler import crawl_news
from pipeline.analyzer import aggregate_and_propagate_scores, analyze_and_map_news
from dotenv import load_dotenv

load_dotenv()

# Flag chạy init
if os.getenv("RUN_INIT_ON_START", "true").lower() == "true":
    init_district_boundaries()

def job():
    print("\n>>> START SPECIAL INDICATOR PIPELINE <<<")
    # 1. Thu thập (vào Scoring DB)
    # count = crawl_news()
    count = 0;
    
    # 2. Phân tích & Cross-DB Update
    if count > 0:
        analyze_and_map_news()

    else:
        # Vẫn chạy aggregation để refresh dữ liệu cũ
        print("Không có báo mới, chạy refresh điểm Cross-DB...")
        
        score_db = ScoringSession()
        aggregate_and_propagate_scores(score_db)
        score_db.close()
        
    print(">>> END PIPELINE <<<\n")

job() # Test run
schedule.every(3).days.do(job)

print("Special Indicator Service is running...")
while True:
    schedule.run_pending()
    time.sleep(60)