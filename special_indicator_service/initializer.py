import osmnx as ox
from sqlalchemy import text
from shapely.geometry import MultiPolygon
from config.config import OSM_DISTRICT_QUERIES
from config.scoring_db_config import ScoringSession

def init_district_boundaries():
    print("--- [Initializer] Đang tải ranh giới quận từ OSM (vào Scoring DB) ---")
    db = ScoringSession()
    
    count = 0
    for query in OSM_DISTRICT_QUERIES:
        try:
            gdf = ox.geocode_to_gdf(query)
            district_name = query.split(',')[0]
            
            geom = gdf.iloc[0].geometry
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon([geom])
                
            wkt_geom = geom.wkt
            
            # Lưu vào Scoring DB
            sql = text("""
                INSERT INTO district_special_stats (district_name, boundary, last_analyzed_at)
                VALUES (:name, ST_Multi(ST_GeomFromText(:wkt, 4326)), NOW())
                ON CONFLICT (district_name) 
                DO UPDATE SET boundary = EXCLUDED.boundary;
            """)
            
            db.execute(sql, {"name": district_name, "wkt": wkt_geom})
            db.commit()
            print(f"    + Updated boundary for: {district_name}")
            count += 1
            
        except Exception as e:
            print(f"    ! Failed to fetch {query}: {e}")
            
    db.close()
    print(f"--- [Initializer] Hoàn tất. Đã cập nhật {count} quận. ---")

if __name__ == "__main__":
    init_district_boundaries()