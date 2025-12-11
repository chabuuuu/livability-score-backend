from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, BigInteger
from geoalchemy2 import Geometry
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Giả sử bạn dùng chung Base, nếu tách file base thì import từ đó
# Nếu không, khai báo Base tại chỗ hoặc import từ config
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class Amenity(Base):
    __tablename__ = "amenities"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    district = Column(String(100))
    amenity_type = Column(String(100))
    
    # Tọa độ số
    longitude = Column(Numeric(11, 8), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    
    # PostGIS Geometry (Quan trọng cho search)
    location = Column(Geometry('POINT', srid=4326))
    
    # Thông tin phụ
    all_tags = Column(Text)
    source = Column(String(50))
    vicinity = Column(Text)
    
    # Google Maps Info
    google_place_id = Column(String(255), unique=True)
    google_rating = Column(Numeric(3, 1))
    google_user_ratings_total = Column(Integer, default=0)
    google_types = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())