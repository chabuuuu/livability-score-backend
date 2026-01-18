import time
from sqlalchemy import text, func
from calculator import LivabilityCalculator
from config.property_service_db_config import get_property_service_db
from config.scoring_service_db_config import get_scoring_service_db
from model.PropertyLivabilityScore import PropertyLivabilityScore # Import model để check max id

# CẤU HÌNH BATCH
BATCH_SIZE = 100 # Số lượng BĐS tính toán trước khi commit (Tăng lên 500-1000 nếu máy khỏe)

def get_last_processed_id(scoring_db):
    """Tìm ID lớn nhất đã được tính điểm để chạy tiếp"""
    try:
        last_id = scoring_db.query(func.max(PropertyLivabilityScore.property_id)).scalar()
        return last_id if last_id is not None else 0
    except Exception as e:
        print(f"Không check được last ID, sẽ chạy từ đầu: {e}")
        return 0

def run_optimized_batch():
    scoring_db = get_scoring_service_db()
    property_db = get_property_service_db()
    
    try:
        print("--- KHỞI TẠO BATCH PROCESS ---")
        
        # 1. Auto Resume: Tìm điểm bắt đầu
        # start_id = get_last_processed_id(scoring_db)
        start_id = 1
        print(f"🔄 Hệ thống phát hiện đã xử lý đến ID: {start_id}")
        print(f"➡️ Sẽ bắt đầu tính toán từ ID: {start_id + 1}")

        # 2. Đếm tổng số lượng cần xử lý
        count_query = text("SELECT COUNT(id) FROM properties WHERE id > :start_id")
        remaining_count = property_db.execute(count_query, {"start_id": start_id}).scalar()
        print(f"📊 Số lượng còn lại: {remaining_count} bất động sản.")

        if remaining_count == 0:
            print("✅ Đã hoàn thành tất cả!")
            return

        calculator = LivabilityCalculator(property_db, scoring_db)
        
        # 3. Vòng lặp xử lý theo Batch
        # Dùng server-side cursor hoặc limit/offset để lấy từng cục ID
        processed_count = 0
        total_time = 0
        
        while True:
            batch_start_time = time.time()
            
            # Lấy 1 gói ID tiếp theo
            query = text("""
                SELECT id FROM properties 
                WHERE id > :start_id 
                ORDER BY id ASC 
                LIMIT :batch_size
            """)
            
            result = property_db.execute(query, {
                "start_id": start_id, 
                "batch_size": BATCH_SIZE
            }).scalars().all()
            
            current_batch_ids = list(result)
            
            if not current_batch_ids:
                break # Hết dữ liệu
                
            print(f"\n🚀 Đang xử lý Batch {len(current_batch_ids)} căn (Từ ID {current_batch_ids[0]} -> {current_batch_ids[-1]})...")
            
            # --- LOOP TRONG BATCH ---
            batch_errors = 0
            for pid in current_batch_ids:
                try:
                    # QUAN TRỌNG: auto_commit=False
                    # Chúng ta chỉ tính toán và add vào session, chưa ghi xuống ổ cứng
                    calculator.calculate_for_property(pid, auto_commit=False)
                except Exception as e:
                    print(f" [x] Lỗi ID {pid}: {e}")
                    batch_errors += 1
            
            # --- COMMIT 1 LẦN CHO CẢ BATCH ---
            try:
                commit_start = time.time()
                scoring_db.commit() # Ghi 1000 dòng xuống DB 1 lần
                commit_time = time.time() - commit_start
            except Exception as e:
                print(f" ❌ Lỗi Commit Batch: {e}")
                scoring_db.rollback()
                # Có thể thêm logic chạy lại từng cái ở đây nếu cần thiết
            
            # Cập nhật con trỏ để vòng lặp sau lấy tiếp
            start_id = current_batch_ids[-1]
            processed_count += len(current_batch_ids)
            
            batch_duration = time.time() - batch_start_time
            total_time += batch_duration
            
            # Log tiến độ
            avg_speed = batch_duration / len(current_batch_ids)
            print(f" ✅ Xong Batch. Time: {batch_duration:.2f}s (Avg: {avg_speed:.4f}s/item). Commit tốn: {commit_time:.2f}s")
            
            # Ước lượng thời gian còn lại
            items_left = remaining_count - processed_count
            est_seconds = items_left * avg_speed
            est_min = est_seconds / 60
            print(f" ⏳ Tiến độ: {processed_count}/{remaining_count}. Còn khoảng: {est_min:.1f} phút.")

    except KeyboardInterrupt:
        print("\n🛑 Đã dừng thủ công. Dữ liệu batch cuối cùng đã được lưu an toàn.")
    except Exception as e:
        print(f"❌ Lỗi Fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        property_db.close()
        scoring_db.close()
        print("--- KẾT THÚC PHIÊN ---")

if __name__ == "__main__":
    run_optimized_batch()