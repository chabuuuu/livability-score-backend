from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
# Không cần import cast, Geography, Geometry nữa
from geoalchemy2 import Geometry

from config.scoring_db_config import get_scoring_db
from model.amenity import Amenity
from schema.common import APIResponse, ResponseData
from schema.amenity_schema import AmenityDTO

router = APIRouter(prefix="/api/v1/recommendation/amenities", tags=["Amenities"])

@router.get("/search/map", response_model=APIResponse[AmenityDTO])
def get_amenities_in_bounds(
    minLat: float = Query(..., description="Vĩ độ nhỏ nhất (Góc dưới trái)"),
    minLng: float = Query(..., description="Kinh độ nhỏ nhất (Góc dưới trái)"),
    maxLat: float = Query(..., description="Vĩ độ lớn nhất (Góc trên phải)"),
    maxLng: float = Query(..., description="Kinh độ lớn nhất (Góc trên phải)"),
    category: str = Query(None, description="Lọc theo loại"),
    limit: int = Query(100, description="Giới hạn số lượng"),
    db: Session = Depends(get_scoring_db)
):
    try:
        # 1. Tạo Bounding Box
        bbox = func.ST_MakeEnvelope(minLng, minLat, maxLng, maxLat, 4326)

        # 2. Query Tối ưu
        # Loại bỏ cast(), dùng trực tiếp Amenity.location
        # ST_Within tự động kích hoạt Spatial Index (GIST)
        query = db.query(Amenity).filter(
            func.ST_Within(Amenity.location, bbox)
        )

        # 3. Filter phụ (Category)
        # SQL Performance Tip: Nên để các filter chính xác (equality) lên trước nếu có thể,
        # nhưng với PostGIS, Query Planner thường ưu tiên Spatial Index trước vì nó lọc mạnh hơn.
        if category:
            query = query.filter(Amenity.category == category)

        # 4. Giới hạn & Sắp xếp
        # Lấy những địa điểm tốt nhất (Rating cao) trong khu vực đó
        amenities = query.order_by(Amenity.google_rating.desc().nullslast()).limit(limit).all()

        results = [AmenityDTO.model_validate(a) for a in amenities]

        return APIResponse(
            status="200",
            result="Succeeded",
            data=ResponseData(items=results)
        )

    except Exception as e:
        print(f"Error fetching amenities: {e}")
        return APIResponse(status="500", result="Failed", error=str(e))