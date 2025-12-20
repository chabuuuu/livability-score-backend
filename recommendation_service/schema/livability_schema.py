from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Request Body: Danh sách ID cần lấy
class BatchScoreRequest(BaseModel):
    propertyIds: List[int]
    include_special_factors: bool = Field(default=True, description="Có tính thêm các chỉ số đặc biệt (Ngập, Tai nạn, Tiềm năng) hay không")

# Response DTO
class LivabilityScoreDTO(BaseModel):
    id: int
    property_id: int
    
    # Raw Metrics
    dist_healthcare: Optional[float]
    dist_education: Optional[float]
    count_shopping: Optional[int]
    dist_transportation: Optional[float]
    dist_environment: Optional[float]
    count_entertainment: Optional[int]
    dist_safety: Optional[float]

    # Normalized Component Scores
    score_healthcare: Optional[float]
    score_education: Optional[float]
    score_shopping: Optional[float]
    score_transportation: Optional[float]
    score_environment: Optional[float]
    score_entertainment: Optional[float]
    score_safety: Optional[float]

    # --- NEW: SPECIAL IMPACT SCORES ---
    flood_impact_score: float = Field(default=0.0, description="Điểm trừ do ngập lụt")
    accident_impact_score: float = Field(default=0.0, description="Điểm trừ do tai nạn/an ninh")
    future_project_score: float = Field(default=0.0, description="Điểm cộng tiềm năng hạ tầng")

    # --- NEW FIELD ---
    livability_score: float = 0.0  # Điểm tổng hợp cuối cùng

    update_at: datetime

    class Config:
        from_attributes = True