import schedule
import time
from sqlalchemy import text
from config.database import get_db, SessionLocal
from pipelines.osm_collector import run_osm_pipeline
from pipelines.google_collector import run_google_pipeline
from pipelines.syncer import sync_data_to_main_table, cleanup_old_runs

def job():
    print("\n\n######################################################")
    print("BẮT ĐẦU QUY TRÌNH THU THẬP AMENITIES")
    print("######################################################\n")
    
    db = SessionLocal()
    try:
        # 1. Tạo Run ID mới
        result = db.execute(text("INSERT INTO run_collection_amenities DEFAULT VALUES RETURNING id"))
        run_id = result.scalar()
        db.commit()
        print(f"=== CREATED RUN ID: {run_id} ===")

        # 2. Chạy OSM Pipeline
        run_osm_pipeline(run_id, db)

        # 3. Chạy Google Pipeline
        run_google_pipeline(run_id, db)

        # 4. Gộp và Đồng bộ
        sync_data_to_main_table(run_id, db)

        # 5. Dọn dẹp
        cleanup_old_runs(run_id, db)

        print("\n=== JOB FINISHED SUCCESSFULLY ===")

    except Exception as e:
        print(f"!!! JOB FAILED: {e}")
        db.rollback()
    finally:
        db.close()

# Chạy ngay một lần khi khởi động để test (Optional)
# job()

# Lên lịch chạy mỗi 12 tiếng
schedule.every(12).hours.do(job)

print("Service Amenity Collector đang chạy... (Schedule: 12h/lần)")

while True:
    schedule.run_pending()
    time.sleep(60)