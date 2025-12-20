from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NewsArticleDTO(BaseModel):
    id: int
    title: str
    url: str
    summary: Optional[str] = None
    topic: Optional[str] = None # FLOOD, ACCIDENT, PROJECT
    impact_score: float = 0.0
    sentiment: Optional[str] = None
    published_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class DistrictNewsDTO(BaseModel):
    district_id: int
    district_name: str
    
    # Boundary dưới dạng WKT (Well-Known Text) để FE dùng thư viện map (như mapbox/leaflet) vẽ Polygon
    boundary_wkt: Optional[str] = None 
    
    # Thống kê nhanh để vẽ Heatmap
    stats: dict = Field(
        default_factory=lambda: {
            "flood_score": 0.0, 
            "accident_score": 0.0, 
            "project_score": 0.0,
            "total_news": 0
        }
    )
    
    # Danh sách bài báo thuộc quận này
    articles: List[NewsArticleDTO] = []

    class Config:
        from_attributes = True