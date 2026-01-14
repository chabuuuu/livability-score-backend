import os
import schedule
import time
from sqlalchemy import text
from config.database import SessionLocal
# Import các pipeline
from pipelines.first_step__google_collector import run_google_pipeline
from pipelines.second_step__syncer import sync_data_to_main_table, cleanup_old_runs
from dotenv import load_dotenv

load_dotenv()

CRON_SCHEDULE_HOURS = int(os.getenv("CRON_SCHEDULE_HOURS", 12))

def job():
    print("\n======================================================")
    print("BẮT ĐẦU JOB THU THẬP TIỆN ÍCH")
    print("======================================================\n")
    
    db = SessionLocal()
    try:
        # 1. Tạo Run ID
        result = db.execute(text("INSERT INTO run_collection_amenities DEFAULT VALUES RETURNING id"))
        run_id = result.scalar()
        db.commit()
        print(f">>> Run ID: {run_id}")

        # 2. Chạy Google Pipeline (Quét các khu vực có BĐS)
        run_google_pipeline(run_id, db)

        # 3. Đồng bộ vào bảng chính (Chống trùng lặp bằng Google Place ID)
        sync_data_to_main_table(run_id, db)

        # 4. Dọn dẹp
        cleanup_old_runs(run_id, db)

        print("\n=== JOB FINISHED SUCCESSFULLY ===")

    except Exception as e:
        print(f"!!! JOB FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

# Chạy thử 1 lần khi khởi động container
job()

# Lên lịch
schedule.every(CRON_SCHEDULE_HOURS).hours.do(job)

print(f"Service is running... Schedule: Every {CRON_SCHEDULE_HOURS} hours.")

while True:
    schedule.run_pending()
    time.sleep(60)