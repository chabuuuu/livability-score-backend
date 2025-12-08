from sqlalchemy import Column, Integer, String, Numeric, Text, BigInteger, JSON, DateTime
from geoalchemy2 import Geometry
import datetime

from config.database_config import Base

class Property(Base):
    __tablename__ = "properties"

    # Mapping chính xác với schema bạn cung cấp
    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    listing_type = Column(String(20), nullable=False) # 'for_sale' or 'for_rent'
    price = Column(Numeric(19, 2), nullable=False)
    price_unit = Column(String(20), nullable=False)
    area = Column(Numeric(10, 2), nullable=False)
    property_type = Column(String(50), nullable=False)
    
    # Địa chỉ & Vị trí
    address_street = Column(Text)
    address_ward = Column(String(100))
    address_district = Column(String(100))
    address_city = Column(String(100))
    
    # Cột quan trọng: PostGIS Geometry
    # srid=4326 là chuẩn GPS (Kinh độ/Vĩ độ)
    location = Column(Geometry(geometry_type='POINT', srid=4326))

    # Thông tin phụ
    num_bedrooms = Column(Integer, default=0)
    num_bathrooms = Column(Integer, default=0)
    features = Column(JSON) # jsonb trong DB
    
    # URL hình ảnh (quan trọng để hiển thị thẻ)
    source_url = Column(Text) 
    
    # Thống kê
    view_count = Column(BigInteger, default=0, nullable=False)
    
    posted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)