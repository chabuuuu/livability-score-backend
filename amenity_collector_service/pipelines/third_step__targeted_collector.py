import pandas as pd
import geopandas as gpd
from sqlalchemy import text
from pipelines.first_step__google_collector import (
    scan_target_cells, 
    get_district_boundaries, 
    create_grid,
    CATEGORIES,
    DISTRICT_NAMES
)
import os
from dotenv import load_dotenv
load_dotenv()


# Giới hạn API riêng cho job bổ sung này (ví dụ 500 call) (convert to int)
TARGETED_API_LIMIT = int(os.getenv("MAP_THIRD_STEP_CALL_LIMIT"))      # Giới hạn số request Google mỗi lần chạy


def find_poorest_districts(run_id, db_session, limit=3):
    """
    Tìm 3 quận có ít amenities nhất dựa trên:
    1. Dữ liệu thực tế (bảng amenities)
    2. Dữ liệu raw vừa thu thập (bảng osm_raw & google_raw)
    """
    print("--- [Targeted] Calculating amenity statistics per district...")
    
    # Tên quận trong DB có thể khác chút so với list, ta cố gắng clean
    # Giả định cột 'district' trong DB lưu dạng chuẩn (ví dụ 'Thủ Đức', 'District 1')
    
    sql = text("""
        WITH all_counts AS (
            -- 1. Amenities hiện có
            SELECT district, COUNT(*) as cnt FROM amenities GROUP BY district
            UNION ALL
            -- 2. OSM Raw vừa lấy
            SELECT district, COUNT(*) as cnt FROM osm_raw_amenities WHERE run_id = :run_id GROUP BY district
            UNION ALL
            -- 3. Google Raw vừa lấy (từ gap analysis)
            SELECT district, COUNT(*) as cnt FROM google_raw_amenities WHERE run_id = :run_id GROUP BY district
        )
        SELECT district, SUM(cnt) as total_amenities
        FROM all_counts
        WHERE district IS NOT NULL AND district != ''
        GROUP BY district
        ORDER BY total_amenities ASC
    """)
    
    result = db_session.execute(sql, {"run_id": run_id}).fetchall()
    
    # Chuẩn hóa danh sách kết quả về format của DISTRICT_NAMES để map với boundaries
    # Ví dụ DB trả về 'District 1', ta cần map về 'District 1, Ho Chi Minh City, Vietnam'
    
    district_stats = []
    for row in result:
        db_dist = row.district
        # Tìm tên đầy đủ tương ứng trong danh sách DISTRICT_NAMES
        full_name = next((name for name in DISTRICT_NAMES if name.startswith(db_dist + ",") or name == db_dist), None)
        
        # Nếu không tìm thấy match chính xác, thử tìm theo contains
        if not full_name:
             full_name = next((name for name in DISTRICT_NAMES if db_dist in name), None)
             
        if full_name:
            district_stats.append({
                "district_name": db_dist, # Tên ngắn (để query/log)
                "full_name": full_name,   # Tên đầy đủ (để lấy boundary OSM)
                "count": row.total_amenities
            })
    
    # Lấy top 3 thấp nhất
    # Lưu ý: Cần lọc chỉ lấy những quận nằm trong danh sách quan tâm của chúng ta
    target_districts = district_stats[:limit]
    
    print("--- [Targeted] Top districts with lowest amenities:")
    for d in target_districts:
        print(f"    - {d['district_name']}: ~{d['count']} amenities")
        
    return target_districts

def run_targeted_pipeline(run_id, db_session):
    print(f"\n--- [Targeted Pipeline] Starting Supplemental Scan for Run ID: {run_id} ---")
    
    # 1. Tìm 3 quận yếu nhất
    targets = find_poorest_districts(run_id, db_session)
    if not targets:
        print("--- [Targeted] No districts found or stats are empty.")
        return

    target_full_names = [t['full_name'] for t in targets]
    
    # 2. Lấy Boundary cho 3 quận này
    # Ta tái sử dụng hàm get_district_boundaries nhưng cần sửa nó chút để nhận list tên
    # Tuy nhiên hàm cũ hardcode DISTRICT_NAMES. 
    # Ở đây ta gọi hàm helper nội bộ (cần copy logic osmnx nhỏ ra đây hoặc import nếu đã tách)
    # Để đơn giản, ta gọi lại hàm import và filter
    
    full_districts_gdf = get_district_boundaries(db_session) # Lấy hết boundary
    if full_districts_gdf is None: return

    # Lọc chỉ lấy 3 quận mục tiêu
    # district_name trong gdf là tên ngắn (do hàm get_district_boundaries split(',')[0])
    target_short_names = [t['district_name'] for t in targets]
    target_gdf = full_districts_gdf[full_districts_gdf['district_name'].isin(target_short_names)]
    
    if target_gdf.empty:
        print("--- [Targeted] Could not match boundaries for target districts.")
        return

    # 3. Tạo lưới phủ kín 3 quận này
    # Không cần check BĐS hay OSM sparse nữa, quét phủ (full coverage)
    grid_gdf = create_grid(target_gdf)
    
    print(f"--- [Targeted] Created grid with {len(grid_gdf)} cells for supplementary scan.")
    
    # 4. Tạo danh sách Task (Grid Cells x Categories)
    # Vì là quét bổ sung cho vùng thiếu dữ liệu, ta nên quét các loại quan trọng
    PRIORITY_CATEGORIES = ['healthcare', 'education', 'shopping', 'entertainment'] # Có thể giảm bớt cate nếu sợ tốn quota
    
    tasks = []
    # Cross join Grid x Categories
    # grid_gdf có cột 'cell_id', 'geometry', 'district_name'
    
    # Để tạo dataframe tasks tương thích với hàm scan_target_cells
    # Ta nhân bản grid cho mỗi category
    for cat in PRIORITY_CATEGORIES:
        temp_df = grid_gdf.copy()
        temp_df['category'] = cat
        tasks.append(temp_df)
        
    tasks_df = pd.concat(tasks, ignore_index=True)
    
    print(f"--- [Targeted] Generated {len(tasks_df)} scan tasks.")
    
    # 5. Thực hiện quét và lưu vào google_raw_amenities
    # Hàm scan_target_cells đã có logic chống lỗi và sleep
    total_saved = scan_target_cells(tasks_df, run_id, db_session, limit=TARGETED_API_LIMIT)
    
    print(f"--- [Targeted Pipeline] Finished. Added {total_saved} supplemental amenities.")