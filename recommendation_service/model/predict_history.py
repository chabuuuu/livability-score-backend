from sqlalchemy import Column, BigInteger, Numeric, String, DateTime, Integer, Text
from geoalchemy2 import Geometry
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Sử dụng Base chung hoặc khai báo mới tùy cấu trúc project của bạn
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class PredictHistory(Base):
    __tablename__ = "predict_histories"

    id = Column(BigInteger, primary_key=True, index=True)
    prediction_id = Column(String(150), index=True)
    user_id = Column(BigInteger, index=True, nullable=True)
    
    # Location
    longitude = Column(Numeric(11, 8))
    latitude = Column(Numeric(10, 8))
    address_district = Column(String(100))
    location = Column(Geometry('POINT', srid=4326))

    # Input Features
    area = Column(Numeric(15, 2))
    num_bedrooms = Column(Numeric(5, 1))
    num_bathrooms = Column(Numeric(5, 1))
    num_floors = Column(Numeric(5, 1))
    facade_width_m = Column(Numeric(10, 2))
    road_width_m = Column(Numeric(10, 2))
    property_type = Column(String(50))
    legal_status = Column(String(100))
    house_direction = Column(String(50))
    balcony_direction = Column(String(50))
    furniture_status = Column(String(100))

    # Prediction Results
    predicted_price = Column(Numeric(20, 2))
    predicted_price_billions = Column(Numeric(15, 2))
    
    # NEW: Lưu nội dung phân tích của AI
    ai_insight = Column(Text) 
    
    # Scores
    livability_score = Column(Numeric(30, 15))
    score_healthcare = Column(Numeric(30, 15))
    score_education = Column(Numeric(30, 15))
    score_transportation = Column(Numeric(30, 15))
    score_environment = Column(Numeric(30, 15))
    score_public_safety = Column(Numeric(30, 15)) 
    score_shopping = Column(Numeric(30, 15))
    score_entertainment = Column(Numeric(30, 15))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())