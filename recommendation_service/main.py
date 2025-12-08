from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc, asc, cast
from typing import List, Optional, Any
from pydantic import BaseModel
from geoalchemy2 import Geography

from config.database_config import get_db, redis_client
from model.property import Property  # IMPORT QUAN TRỌNG

# Import nội bộ


app = FastAPI(title="Real Estate Recommendation Service")

# --- 1. SCHEMAS (Định dạng dữ liệu trả về) ---

class PropertyCard(BaseModel):
    id: int
    title: str
    price: float
    price_unit: str
    area: float
    address: str
    num_bedrooms: Optional[int]
    num_bathrooms: Optional[int]
    thumbnail_url: Optional[str]
    distance_km: float
    recommendation_type: str

    class Config:
        from_attributes = True

# Wrapper cho phần "data" -> "items"
class ResponseData(BaseModel):
    items: List[PropertyCard]

# Wrapper cho toàn bộ response
class APIResponse(BaseModel):
    status: str
    result: str
    error: Optional[str] = None
    data: Optional[ResponseData] = None

# --- 2. LOGIC API ---
@app.get("/api/v1/recommendation/home", response_model=APIResponse)
def get_home_recommendations(
    lat: float = Query(..., description="Vĩ độ người dùng (hoặc vị trí muốn tìm)"),
    lng: float = Query(..., description="Kinh độ người dùng (hoặc vị trí muốn tìm)"),
    limit: int = Query(10, description="Số lượng gợi ý muốn lấy"),
    radius_km: float = Query(5.0, description="Bán kính tìm kiếm (km)"),
    user_id: Optional[int] = Query(None, description="ID người dùng (nếu đã login)"),
    db: Session = Depends(get_db)
):
    try:
        final_results = []
        exclude_ids = []

        # Tạo điểm Geometry từ tọa độ input
        user_location = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)

        # FIX: Định nghĩa biểu thức tính khoảng cách một lần để dùng lại
        # Sử dụng Geography(srid=4326) thay vì func.geography để tránh lỗi caching
        distance_expr = func.ST_Distance(
            cast(Property.location, Geography(srid=4326)), 
            cast(user_location, Geography(srid=4326))
        ).label("distance_meters")

        # --- GIAI ĐOẠN 1: PERSONALIZED (Redis) ---
        if user_id:
            try:
                redis_key = f"rec:home:{user_id}"
                cached_ids = redis_client.zrevrange(redis_key, 0, limit - 1)
                
                if cached_ids:
                    cached_ids = [int(i) for i in cached_ids]
                    
                    personalized_query = db.query(
                        Property,
                        distance_expr # Dùng biến expression đã định nghĩa
                    ).filter(
                        Property.id.in_(cached_ids),
                        func.ST_DWithin(
                            cast(Property.location, Geography(srid=4326)),
                            cast(user_location, Geography(srid=4326)),
                            radius_km * 1000
                        )
                    )
                    
                    fetched_props = personalized_query.all()
                    prop_map = {p.Property.id: p for p in fetched_props}
                    
                    for pid in cached_ids:
                        if pid in prop_map:
                            item, dist_m = prop_map[pid]
                            final_results.append(
                                map_to_schema(item, dist_m, "PERSONALIZED")
                            )
                            exclude_ids.append(pid)
                            
            except Exception as e:
                print(f"Redis Error (Ignored): {e}")

        # --- GIAI ĐOẠN 2: POPULARITY (PostGIS Fallback) ---
        slots_remaining = limit - len(final_results)
        
        if slots_remaining > 0:
            fallback_query = db.query(
                Property,
                distance_expr # Dùng lại biến expression
            ).filter(
                func.ST_DWithin(
                    cast(Property.location, Geography(srid=4326)),
                    cast(user_location, Geography(srid=4326)),
                    radius_km * 1000
                )
            )
            
            if exclude_ids:
                fallback_query = fallback_query.filter(~Property.id.in_(exclude_ids))
                
            # FIX: Dùng trực tiếp object expression trong order_by thay vì string alias
            fallback_query = fallback_query.order_by(
                desc(Property.view_count),
                asc(distance_expr) 
            ).limit(slots_remaining)
            
            popular_props = fallback_query.all()
            
            for item, dist_m in popular_props:
                final_results.append(
                    map_to_schema(item, dist_m, "POPULAR")
                )

        return APIResponse(
            status="200",
            result="Succeeded",
            error=None,
            data=ResponseData(items=final_results)
        )

    except Exception as e:
        import traceback
        traceback.print_exc() # In lỗi ra console để debug nếu cần
        return APIResponse(
            status="500",
            result="Failed",
            error=str(e),
            data=None
        )

# --- Helper Function ---
def map_to_schema(prop_obj, distance_meters, rec_type):
    full_addr = f"{prop_obj.address_street or ''}, {prop_obj.address_ward or ''}, {prop_obj.address_district or ''}"
    
    # Xử lý trường hợp thumbnail_url None
    thumb = prop_obj.source_url
    
    return PropertyCard(
        id=prop_obj.id,
        title=prop_obj.title,
        price=float(prop_obj.price) if prop_obj.price else 0.0,
        price_unit=prop_obj.price_unit or "",
        area=float(prop_obj.area) if prop_obj.area else 0.0,
        address=full_addr,
        num_bedrooms=prop_obj.num_bedrooms,
        num_bathrooms=prop_obj.num_bathrooms,
        thumbnail_url=thumb,
        distance_km=round(distance_meters / 1000, 2) if distance_meters else 0.0,
        recommendation_type=rec_type
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)