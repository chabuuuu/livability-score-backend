import os
import schedule
import time
from sqlalchemy import text
from config.database import SessionLocal
# Import các pipeline
from pipelines.first_step__osm_collector import run_osm_pipeline
from pipelines.second_step__google_collector import run_google_pipeline
from pipelines.third_step__targeted_collector import run_targeted_pipeline # <-- MỚI
from pipelines.fourth_step__syncer import sync_data_to_main_table, cleanup_old_runs
from dotenv import load_dotenv

load_dotenv()

CRON_SCHEDULE_HOURS = int(os.getenv("CRON_SCHEDULE_HOURS", 12))

def job():
    print("\n\n######################################################")
    print("BẮT ĐẦU QUY TRÌNH THU THẬP AMENITIES (FULL PIPELINE)")
    print("######################################################\n")
    
    # Lấy session thủ công cho job
    db = SessionLocal()
    try:
        # 1. Tạo Run ID mới
        result = db.execute(text("INSERT INTO run_collection_amenities DEFAULT VALUES RETURNING id"))
        run_id = result.scalar()
        db.commit()
        print(f"=== CREATED RUN ID: {run_id} ===")

        # 2. Chạy OSM Pipeline (Cào diện rộng miễn phí)
        run_osm_pipeline(run_id, db)

        # 3. Chạy Google Pipeline (Gap Analysis - Quét lỗ hổng có BĐS)
        run_google_pipeline(run_id, db)
        
        # 4. Chạy Targeted Pipeline (Bổ sung dữ liệu cho 3 quận nghèo nàn nhất)
        run_targeted_pipeline(run_id, db)

        # 5. Gộp và Đồng bộ vào bảng chính
        sync_data_to_main_table(run_id, db)

        # 6. Dọn dẹp dữ liệu raw cũ
        cleanup_old_runs(run_id, db)

        print("\n=== JOB FINISHED SUCCESSFULLY ===")

    except Exception as e:
        print(f"!!! JOB FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

# Chạy ngay một lần để test (Comment lại nếu deploy production)
job()

# Lên lịch
schedule.every(CRON_SCHEDULE_HOURS).hours.do(job)

print(f"Service Amenity Collector đang chạy... (Schedule: {CRON_SCHEDULE_HOURS}h/lần)")

while True:
    schedule.run_pending()
    time.sleep(60)