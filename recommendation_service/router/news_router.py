from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List

from config.property_db_config import get_property_db
from config.scoring_db_config import get_scoring_db
from model.property import Property
from schema.common import APIResponse, ResponseData
from schema.news_schema import DistrictNewsDTO, NewsArticleDTO

router = APIRouter(prefix="/api/v1/recommendation/news", tags=["News & Insights"])

@router.get("/map", response_model=APIResponse[DistrictNewsDTO])
def get_district_news_in_bounds(
    minLat: float = Query(..., description="Vĩ độ nhỏ nhất (Góc dưới trái)"),
    minLng: float = Query(..., description="Kinh độ nhỏ nhất (Góc dưới trái)"),
    maxLat: float = Query(..., description="Vĩ độ lớn nhất (Góc trên phải)"),
    maxLng: float = Query(..., description="Kinh độ lớn nhất (Góc trên phải)"),
    topic: str = Query(None, description="Lọc theo chủ đề: FLOOD, ACCIDENT, PROJECT"),
    db: Session = Depends(get_scoring_db)
):
    """
    Lấy danh sách các Quận nằm trong khung nhìn bản đồ, kèm theo:
    - Ranh giới (Boundary) để vẽ highlight.
    - Danh sách bài báo (News) liên quan.
    - Điểm thống kê (Stats) để vẽ Heatmap.
    """
    try:
        # 1. Tìm các Quận nằm trong Bounding Box
        # Sử dụng ST_MakeEnvelope để tạo hình chữ nhật từ tọa độ view
        # Sử dụng ST_Intersects để tìm quận giao cắt với view đó
        district_sql = text("""
            SELECT 
                d.id, d.district_name, 
                ST_AsText(d.boundary) as boundary_wkt,
                d.flood_impact_score, d.accident_impact_score, d.future_project_score
            FROM district_special_stats d
            WHERE d.boundary IS NOT NULL 
            AND ST_Intersects(
                d.boundary, 
                ST_MakeEnvelope(:minLng, :minLat, :maxLng, :maxLat, 4326)
            )
        """)
        
        districts = db.execute(district_sql, {
            "minLat": minLat, "minLng": minLng,
            "maxLat": maxLat, "maxLng": maxLng
        }).fetchall()
        
        if not districts:
            return APIResponse(status="200", result="Succeeded", data=ResponseData(items=[]))

        # Danh sách ID các quận tìm thấy
        district_ids = [d.id for d in districts]
        
        # 2. Lấy bài báo thuộc các quận này (Query 1 lần tối ưu)
        news_sql_query = """
            SELECT 
                id, district_id, title, url, summary, topic, 
                impact_score, sentiment, published_date
            FROM news_articles
            WHERE district_id IN :d_ids
        """
        params = {"d_ids": tuple(district_ids)}
        
        # Thêm filter topic nếu có
        if topic:
            news_sql_query += " AND topic = :topic"
            params["topic"] = topic
            
        # Lấy bài báo mới nhất trước
        news_sql_query += " ORDER BY published_date DESC LIMIT 200"
        
        news_query = text(news_sql_query)
        news_records = db.execute(news_query, params).fetchall()
        
        # 3. Gom nhóm bài báo theo District ID (In-memory grouping)
        news_map = {d_id: [] for d_id in district_ids}
        for n in news_records:
            article_dto = NewsArticleDTO(
                id=n.id,
                title=n.title,
                url=n.url,
                summary=n.summary,
                topic=n.topic,
                impact_score=float(n.impact_score or 0),
                sentiment=n.sentiment,
                published_date=n.published_date
            )
            news_map[n.district_id].append(article_dto)

        # 4. Tạo kết quả trả về
        results = []
        for d in districts:
            articles = news_map.get(d.id, [])
            
            dto = DistrictNewsDTO(
                district_id=d.id,
                district_name=d.district_name,
                boundary_wkt=d.boundary_wkt,
                stats={
                    "flood_score": float(d.flood_impact_score or 0),
                    "accident_score": float(d.accident_impact_score or 0),
                    "project_score": float(d.future_project_score or 0),
                    "total_news": len(articles)
                },
                articles=articles
            )
            results.append(dto)

        return APIResponse(
            status="200",
            result="Succeeded",
            data=ResponseData(items=results)
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return APIResponse(status="500", result="Failed", error=str(e))
    
@router.get("/property/{property_id}", response_model=APIResponse[NewsArticleDTO])
def get_news_by_property(
    property_id: int,
    topic: str = Query(None, description="Lọc theo chủ đề: FLOOD, ACCIDENT, PROJECT"),
    limit: int = Query(10, description="Giới hạn số lượng bài báo"),
    scoring_db: Session = Depends(get_scoring_db),
    property_db: Session = Depends(get_property_db)
):
    """
    Lấy danh sách bài báo liên quan đến một Bất động sản cụ thể.
    Logic: Tìm quận chứa BĐS này (Spatial Query) -> Lấy báo của quận đó.
    Giúp giải thích 'Tại sao nhà này có điểm số như vậy?'.
    """
    try:
        # 1. Lấy vị trí BĐS từ Property DB
        # Sử dụng ST_AsText để lấy WKT
        prop_loc_wkt = property_db.query(func.ST_AsText(Property.location)).filter(Property.id == property_id).scalar()
        
        if not prop_loc_wkt:
             return APIResponse(status="404", result="Failed", error="Property not found or has no location")

        # 2. Tìm Quận chứa BĐS này trong Scoring DB (Cross-DB Spatial Query)
        # Sử dụng ST_Intersects để kiểm tra điểm nằm trong vùng nào
        district_query = text("""
            SELECT id 
            FROM district_special_stats 
            WHERE boundary IS NOT NULL 
            AND ST_Intersects(boundary, ST_GeomFromText(:wkt, 4326))
            LIMIT 1
        """)
        
        district_id = scoring_db.execute(district_query, {"wkt": prop_loc_wkt}).scalar()
        
        if not district_id:
             # Trường hợp không thuộc quận nào trong DB
             return APIResponse(status="200", result="Succeeded", data=ResponseData(items=[]))

        # 3. Lấy tin tức của quận đó
        news_sql = """
            SELECT 
                id, title, url, summary, topic, 
                impact_score, sentiment, published_date
            FROM news_articles
            WHERE district_id = :did
        """
        params = {"did": district_id, "limit": limit}
        
        if topic:
            news_sql += " AND topic = :topic"
            params["topic"] = topic
            
        news_sql += " ORDER BY published_date DESC LIMIT :limit"
        
        news_records = scoring_db.execute(text(news_sql), params).fetchall()
        
        # 4. Map sang DTO
        results = [
            NewsArticleDTO(
                id=n.id,
                title=n.title,
                url=n.url,
                summary=n.summary,
                topic=n.topic,
                impact_score=float(n.impact_score or 0),
                sentiment=n.sentiment,
                published_date=n.published_date
            ) for n in news_records
        ]

        return APIResponse(
            status="200",
            result="Succeeded",
            data=ResponseData(items=results)
        )

    except Exception as e:
        return APIResponse(status="500", result="Failed", error=str(e))