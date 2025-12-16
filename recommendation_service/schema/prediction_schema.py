from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class PropertyPredictionRequest(BaseModel):
    # Location (Để tính Livability Score)
    latitude: float = Field(..., description="Vĩ độ", example=10.7725)
    longitude: float = Field(..., description="Kinh độ", example=106.6980)
    address_district: str = Field(..., description="Quận (VD: Quận 1, Quận 7)", example="Quận 1")
    full_address: Optional[str] = Field(..., description="Địa chỉ đầy đủ", example="123 Đường ABC, Phường XYZ, Quận 1, TP.HCM")

    # Đặc điểm vật lý (Physical Attributes)
    area: float = Field(..., gt=0, description="Diện tích (m2)")
    num_bedrooms: float = Field(default=1.0)
    num_bathrooms: float = Field(default=1.0)
    num_floors: float = Field(default=1.0)
    facade_width_m: float = Field(default=0.0, description="Độ rộng mặt tiền (m)")
    road_width_m: float = Field(default=0.0, description="Độ rộng đường trước nhà (m)")
    
    # Đặc điểm phân loại (Categorical Attributes)
    property_type: str = Field(..., description="apartment, house, villa...")
    legal_status: str = Field(default="Sổ hồng")
    house_direction: Optional[str] = Field(default=None, description="Hướng nhà (Đông, Tây...)")
    balcony_direction: Optional[str] = Field(default=None, description="Hướng ban công")
    furniture_status: Optional[str] = Field(default=None, description="Nội thất (Đầy đủ, Cơ bản...)")

class PredictionResponse(BaseModel):
    prediction_id: str # ID định danh cho phiên dự đoán này (dùng để chat tiếp)
    predicted_price: float
    predicted_price_billions: float
    livability_score: float
    component_scores: Dict[str, float]
    ai_insight: str # Lời giải thích của AI

class ChatPredictionRequest(BaseModel):
    prediction_id: str # UUID nhận được từ API /price
    message: str

class ChatMessageDTO(BaseModel):
    role: str
    text: str


class PredictHistoryDTO(BaseModel):
    prediction_id: str
    created_at: datetime
    address_district: str
    area: float
    property_type: str
    predicted_price_billions: float
    livability_score: float
    ai_insight: Optional[str] = None

    longitude: float
    latitude: float
    address_district: str
    full_address: Optional[str] = None

    # Input Features
    area: float
    num_bedrooms: float
    num_bathrooms: float
    num_floors: float
    facade_width_m: float
    road_width_m: float
    property_type: str
    legal_status: str
    house_direction: Optional[str] = None
    balcony_direction: Optional[str] = None
    furniture_status: Optional[str] = None

    component_scores: Dict[str, float] 
    
    class Config:
        from_attributes = True # Cho phép mapping từ ORM Object