from sqlalchemy import Column, BigInteger, Numeric, ForeignKey, DateTime, UniqueConstraint, Integer
from sqlalchemy.sql import func
from config.scoring_service_db_config import Base


class PropertyLivabilityScore(Base):
    __tablename__ = "property_livability_scores"

    id = Column(BigInteger, primary_key=True, index=True)
    property_id = Column(BigInteger, nullable=False, unique=True)
    
    # --- CHỈ SỐ THÔ (RAW METRICS) ---
    # Lưu lại để phục vụ phân tích hoặc tính toán lại trọng số sau này
    dist_healthcare = Column(Numeric(10, 2))      # Khoảng cách đến y tế gần nhất (mét)
    dist_education = Column(Numeric(10, 2))       # Khoảng cách đến giáo dục gần nhất (mét)
    count_shopping = Column(Integer, default=0)   # Số lượng tiện ích mua sắm trong bán kính
    dist_transportation = Column(Numeric(10, 2))  # Khoảng cách đến giao thông công cộng (mét)
    dist_environment = Column(Numeric(10, 2))     # Khoảng cách đến công viên/không gian xanh (mét)
    count_entertainment = Column(Integer, default=0) # Số lượng tiện ích giải trí trong bán kính
    dist_safety = Column(Numeric(10, 2))          # Khoảng cách đến đồn công an/PCCC (mét)

    # --- ĐIỂM THÀNH PHẦN ĐÃ CHUẨN HÓA (0-100) ---
    score_healthcare = Column(Numeric(5, 2), default=0)
    score_education = Column(Numeric(5, 2), default=0)
    score_shopping = Column(Numeric(5, 2), default=0)
    score_transportation = Column(Numeric(5, 2), default=0)
    score_environment = Column(Numeric(5, 2), default=0)
    score_entertainment = Column(Numeric(5, 2), default=0)
    score_safety = Column(Numeric(5, 2), default=0)
