import schedule
import time
from sqlalchemy import text
from config.database import SessionLocal
# Import các pipeline
from pipelines.first_step__osm_collector import run_osm_pipeline
from pipelines.second_step__google_collector import run_google_pipeline
from pipelines.third_step__targeted_collector import run_targeted_pipeline # <-- MỚI
from pipelines.fourth_step__syncer import sync_data_to_main_table, cleanup_old_runs

def job():
    print("\n\n######################################################")
    print("BẮT ĐẦU QUY TRÌNH THU THẬP AMENITIES (FULL PIPELINE)")
    print("######################################################\n")
    
    # Lấy session thủ công cho job
    db = SessionLocal()
    try:
        # 1. Tạo Run ID mới
        # result = db.execute(text("INSERT INTO run_collection_amenities DEFAULT VALUES RETURNING id"))
        run_id = 1
        # db.commit()
        print(f"=== CREATED RUN ID: {run_id} ===")

        # 2. Chạy OSM Pipeline (Cào diện rộng miễn phí)
        # run_osm_pipeline(run_id, db)

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
schedule.every(12).hours.do(job)

print("Service Amenity Collector đang chạy... (Schedule: 12h/lần)")

while True:
    schedule.run_pending()
    time.sleep(60)