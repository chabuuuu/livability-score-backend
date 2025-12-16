from sqlalchemy import text
from sqlalchemy.orm import Session

def sync_data_to_main_table(run_id: int, db: Session):
    print(f"--- [Sync] Bắt đầu đồng bộ dữ liệu từ Run ID: {run_id} ---")

    # BƯỚC 1: UPSERT TỪ OSM RAW
    # Logic chống trùng: Trùng vị trí (bán kính 10m) VÀ Trùng tên (Similiarity > 0.8) -> UPDATE
    # Nếu không -> INSERT
    # Sử dụng PostGIS ST_DWithin và pg_trgm (cần enable extension)
    
    print("    -> Đồng bộ dữ liệu OSM...")
    osm_sync_sql = text("""
        INSERT INTO amenities (
            name, category, district, amenity_type, longitude, latitude, 
            all_tags, source, created_at, updated_at, location
        )
        SELECT 
            raw.name, raw.category, raw.district, raw.amenity_type, raw.longitude, raw.latitude, 
            raw.all_tags, 'OSM', NOW(), NOW(), raw.location
        FROM osm_raw_amenities raw
        WHERE raw.run_id = :run_id
        ON CONFLICT (id) DO UPDATE SET -- Mẹo: dùng conflict ID thì không đúng logic spatial
        -- Sửa lại logic dùng MERGE hoặc INSERT WHERE NOT EXISTS cho chuẩn không gian
        -- Ở đây ta dùng logic check không gian:
        -- Nếu tìm thấy điểm main nào cách điểm raw < 20m VÀ tên giống nhau => UPDATE
        -- Nếu không => INSERT
        -- Tuy nhiên PostgreSQL standard Insert không support Where Not Exists Spatial complex
        -- Nên ta sẽ dùng Temporary Table hoặc logic code.
        -- Dưới đây là cách dùng UPSERT giả lập bằng CTE:
    """)
    
    # --- LOGIC TỐI ƯU HƠN CHO SYNC SPATIAL ---
    # 1. Update các điểm đã tồn tại (Match vị trí < 30m và Tên tương tự)
    update_osm_sql = text("""
        UPDATE amenities main
        SET 
            updated_at = NOW(),
            all_tags = raw.all_tags,
            amenity_type = raw.amenity_type -- Cập nhật loại nếu chi tiết hơn
        FROM osm_raw_amenities raw
        WHERE raw.run_id = :run_id
        AND ST_DWithin(main.location, raw.location, 30) -- Trùng trong 30m
        AND (main.name ILIKE raw.name OR main.name % raw.name) -- Cần extension pg_trgm
    """)
    db.execute(update_osm_sql, {"run_id": run_id})
    
    # 2. Insert các điểm mới (Chưa tồn tại trong main)
    insert_osm_sql = text("""
        INSERT INTO amenities (
            name, category, district, amenity_type, longitude, latitude, 
            all_tags, source, created_at, updated_at, location
        )
        SELECT 
            raw.name, raw.category, raw.district, raw.amenity_type, raw.longitude, raw.latitude, 
            raw.all_tags, 'OSM', NOW(), NOW(), raw.location
        FROM osm_raw_amenities raw
        WHERE raw.run_id = :run_id
        AND NOT EXISTS (
            SELECT 1 FROM amenities main 
            WHERE ST_DWithin(main.location, raw.location, 30)
            AND (main.name ILIKE raw.name OR main.name = raw.name)
        )
    """)
    result_osm = db.execute(insert_osm_sql, {"run_id": run_id})
    print(f"    -> [OSM Sync] Đã thêm mới {result_osm.rowcount} địa điểm.")

    # BƯỚC 2: UPSERT TỪ GOOGLE RAW
    # Ưu tiên Google Place ID để chống trùng
    print("    -> Đồng bộ dữ liệu Google...")
    google_sync_sql = text("""
        INSERT INTO amenities (
            name, category, district, amenity_type, longitude, latitude, 
            google_place_id, google_rating, google_types, vicinity, all_tags,
            source, created_at, updated_at, location
        )
        SELECT 
            name, category, district, amenity_type, longitude, latitude,
            google_place_id, google_rating, google_types, vicinity, all_tags,
            'google_places', NOW(), NOW(), location
        FROM google_raw_amenities
        WHERE run_id = :run_id
        ON CONFLICT (google_place_id) 
        DO UPDATE SET
            google_rating = EXCLUDED.google_rating,
            google_user_ratings_total = EXCLUDED.google_user_ratings_total,
            updated_at = NOW();
    """)
    # Lưu ý: Cần đảm bảo bảng amenities có UNIQUE INDEX (google_place_id)
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