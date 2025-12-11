import time

from sqlalchemy import text

from calculator import LivabilityCalculator
from config.property_service_db_config import get_property_service_db
from config.scoring_service_db_config import get_scoring_service_db

def run_batch_calculation():
    print("--- BẮT ĐẦU TÍNH TOÁN BATCH LIVABILITY SCORE ---")
    scoring_db = get_scoring_service_db()
    property_db = get_property_service_db()

    
    try:
        # 2. Khởi tạo Calculator
        calculator = LivabilityCalculator(property_db, scoring_db)
        
        # 3. Lấy danh sách tất cả Property ID
        print("Đang lấy danh sách Property ID...")
        # Sử dụng text SQL để query nhanh ID
        query = text("SELECT id FROM properties ORDER BY id ASC")
        result = property_db.execute(query).scalars().all()
        property_ids = list(result)
        
        total_props = len(property_ids)
        print(f"Tìm thấy tổng cộng: {total_props} bất động sản.")
        
        if total_props == 0:
            print("Không có dữ liệu để xử lý.")
            return

        # 4. Duyệt và tính toán (Sử dụng tqdm để hiện thanh loading)
        print("Đang xử lý...")
        start_time = time.time()
        
        success_count = 0
        error_count = 0
        
        # tqdm tạo thanh loading bar trong terminal
        for pid in property_ids:
            try:
                calculator.calculate_for_property(pid)
                success_count += 1
            except Exception as e:
                print(f"\n[!] Lỗi tại Property ID {pid}: {e}")
                error_count += 1
                # Rollback session property nếu có lỗi ghi DB để tránh ảnh hưởng record sau
                property_db.rollback()

        end_time = time.time()
        duration = end_time - start_time
        
        print("\n--- HOÀN THÀNH ---")
        print(f"Tổng thời gian: {duration:.2f} giây")
        print(f"Trung bình: {duration/total_props:.4f} giây/BĐS")
        print(f"Thành công: {success_count}")
        print(f"Thất bại: {error_count}")
        
    except Exception as e:
        print(f"Lỗi Fatal hệ thống: {e}")
    finally:
        # 5. Đóng kết nối
        property_db.close()
        scoring_db.close()

if __name__ == "__main__":
    # Xác nhận trước khi chạy
    confirm = input("Bạn có chắc muốn tính toán lại điểm cho TOÀN BỘ dữ liệu? (y/n): ")
    if confirm.lower() == 'y':
        run_batch_calculation()
    else:
        print("Đã hủy.")