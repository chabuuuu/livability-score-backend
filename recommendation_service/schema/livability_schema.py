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
    dist_healthcare: Optional[float]      # Khoảng cách đến y tế gần nhất (mét)
    count_healthcare: Optional[int] # Số lượng tiện ích y tế trong bán kính
    dist_education: Optional[float]       # Khoảng cách đến giáo dục gần nhất (mét)
    count_education: Optional[int]  # Số lượng tiện ích giáo dục trong bán kính
    count_shopping: Optional[int]   # Số lượng tiện ích mua sắm trong bán kính
    dist_shopping: Optional[float]        # Khoảng cách đến mua sắm gần nhất (mét)
    dist_transportation: Optional[float]  # Khoảng cách đến giao thông công cộng (mét)
    count_transportation: Optional[int] # Số lượng tiện ích giao thông trong bán kính
    dist_environment: Optional[float]     # Khoảng cách đến công viên/không gian xanh (mét)
    count_environment: Optional[int] # Số lượng tiện ích xanh trong bán kính
    count_entertainment: Optional[int] # Số lượng tiện ích giải trí trong bán kính
    dist_entertainment: Optional[float]   # Khoảng cách đến giải trí gần nhất (mét)
    dist_safety: Optional[float]          # Khoảng cách đến đồn công an/PCCC (mét)
    count_safety: Optional[int]     # Số lượng tiện ích đồn công an/PCCC trong bán kính

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