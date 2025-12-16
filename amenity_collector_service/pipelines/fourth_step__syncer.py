from sqlalchemy import text
from sqlalchemy.orm import Session

def sync_data_to_main_table(run_id: int, db: Session):
    print(f"--- [Sync] Bắt đầu đồng bộ dữ liệu từ Run ID: {run_id} ---")

    # BƯỚC 1: UPSERT TỪ OSM RAW (Có xử lý logic không gian)
    print("    -> Đồng bộ dữ liệu OSM...")
    # Update các điểm đã tồn tại (Match vị trí < 30m và Tên tương tự)
    # Lưu ý: Cần DISTINCT ON trong subquery hoặc logic update nếu osm_raw cũng bị trùng
    update_osm_sql = text("""
        UPDATE amenities main
        SET 
            updated_at = NOW(),
            all_tags = raw.all_tags,
            amenity_type = raw.amenity_type
        FROM (
            -- FIX: Lọc trùng OSM raw trước khi join
            SELECT DISTINCT ON (name, location) *
            FROM osm_raw_amenities 
            WHERE run_id = :run_id
        ) raw
        WHERE ST_DWithin(main.location, raw.location, 30)
        AND (main.name ILIKE raw.name OR main.name = raw.name) -- Giản lược logic so sánh tên
    """)
    db.execute(update_osm_sql, {"run_id": run_id})
    
    # Insert các điểm mới
    insert_osm_sql = text("""
        INSERT INTO amenities (
            name, category, district, amenity_type, longitude, latitude, 
            all_tags, source, created_at, updated_at, location
        )
        SELECT 
            raw.name, raw.category, raw.district, raw.amenity_type, raw.longitude, raw.latitude, 
            raw.all_tags, 'OSM', NOW(), NOW(), raw.location
        FROM (
            -- FIX: Lọc trùng OSM raw
            SELECT DISTINCT ON (name, location) *
            FROM osm_raw_amenities 
            WHERE run_id = :run_id
        ) raw
        WHERE NOT EXISTS (
            SELECT 1 FROM amenities main 
            WHERE ST_DWithin(main.location, raw.location, 30)
            AND (main.name ILIKE raw.name OR main.name = raw.name)
        )
    """)
    result_osm = db.execute(insert_osm_sql, {"run_id": run_id})
    print(f"    -> [OSM Sync] Đã thêm mới {result_osm.rowcount} địa điểm.")

    # BƯỚC 2: UPSERT TỪ GOOGLE RAW (SỬA LỖI CARDINALITY VIOLATION)
    print("    -> Đồng bộ dữ liệu Google...")
    
    # Chúng ta sử dụng DISTINCT ON (google_place_id) để đảm bảo mỗi place_id chỉ xuất hiện 1 lần
    # ORDER BY google_place_id, id DESC giúp lấy bản ghi mới nhất nếu có trùng lặp
    google_sync_sql = text("""
        INSERT INTO amenities (
            name, category, district, amenity_type, longitude, latitude, 
            google_place_id, google_rating, google_types, vicinity, all_tags,
            source, created_at, updated_at, location
        )
        SELECT DISTINCT ON (google_place_id)
            name, category, district, amenity_type, longitude, latitude,
            google_place_id, google_rating, google_types, vicinity, all_tags,
            'google_places', NOW(), NOW(), location
        FROM google_raw_amenities
        WHERE run_id = :run_id
        ORDER BY google_place_id, id DESC
        ON CONFLICT (google_place_id) 
        DO UPDATE SET
            google_rating = EXCLUDED.google_rating,
            -- google_user_ratings_total = EXCLUDED.google_user_ratings_total, -- Bỏ dòng này nếu bảng raw chưa có cột này
            updated_at = NOW();
    """)
    
    result_google = db.execute(google_sync_sql, {"run_id": run_id})
    print(f"    -> [Google Sync] Đã xử lý {result_google.rowcount} địa điểm.")

    db.commit()

def cleanup_old_runs(current_run_id: int, db: Session):
    print(f"--- [Cleanup] Xóa dữ liệu raw cũ (giữ lại 2 run gần nhất) ---")
    threshold_id = current_run_id - 2
    
    if threshold_id > 0:
        db.execute(text("DELETE FROM osm_raw_amenities WHERE run_id <= :tid"), {"tid": threshold_id})
        db.execute(text("DELETE FROM google_raw_amenities WHERE run_id <= :tid"), {"tid": threshold_id})
        db.execute(text("DELETE FROM run_collection_amenities WHERE id <= :tid"), {"tid": threshold_id})
        db.commit()
        print("    -> Cleanup hoàn tất.")
    else:
        print("    -> Chưa đủ dữ liệu để cleanup.")