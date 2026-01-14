from sqlalchemy import text
from sqlalchemy.orm import Session

def sync_data_to_main_table(run_id: int, db: Session):
    print(f"--- [Sync] Bắt đầu đồng bộ dữ liệu từ Run ID: {run_id} ---")

    # Sử dụng DISTINCT ON (google_place_id) để loại bỏ trùng lặp trong chính bảng raw trước khi insert
    print("    -> Đồng bộ dữ liệu Google Raw sang bảng chính Amenities...")
    
    google_sync_sql = text("""
        INSERT INTO amenities (
            name, category, district, amenity_type, longitude, latitude, 
            google_place_id, google_rating, google_user_ratings_total, google_types, vicinity, all_tags,
            source, created_at, updated_at, location
        )
        SELECT DISTINCT ON (google_place_id)
            name, category, district, amenity_type, longitude, latitude,
            google_place_id, google_rating, google_user_ratings_total, google_types, vicinity, all_tags,
            'google_places', NOW(), NOW(), location
        FROM google_raw_amenities
        WHERE run_id = :run_id
        ORDER BY google_place_id, id DESC -- Lấy bản ghi mới nhất nếu có trùng trong raw
        ON CONFLICT (google_place_id) 
        DO UPDATE SET
            name = EXCLUDED.name, -- Cập nhật tên nếu Google đổi tên
            google_rating = EXCLUDED.google_rating,
            google_user_ratings_total = EXCLUDED.google_user_ratings_total,
            updated_at = NOW();
    """)
    
    result_google = db.execute(google_sync_sql, {"run_id": run_id})
    db.commit()
    
    print(f"    -> [Sync Hoàn tất] Đã cập nhật/thêm mới {result_google.rowcount} địa điểm.")

def cleanup_old_runs(current_run_id: int, db: Session):
    print(f"--- [Cleanup] Xóa dữ liệu raw cũ ---")
    threshold_id = current_run_id - 2 # Giữ lại 2 run gần nhất để debug
    
    if threshold_id > 0:
        db.execute(text("DELETE FROM google_raw_amenities WHERE run_id <= :tid"), {"tid": threshold_id})
        db.execute(text("DELETE FROM run_collection_amenities WHERE id <= :tid"), {"tid": threshold_id})
        
        db.commit()
        print("    -> Dữ liệu cũ đã được dọn dẹp.")