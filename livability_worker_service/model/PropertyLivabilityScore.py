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
    count_healthcare = Column(Integer, default=0) # Số lượng tiện ích y tế trong bán kính
    dist_education = Column(Numeric(10, 2))       # Khoảng cách đến giáo dục gần nhất (mét)
    count_education = Column(Integer, default=0)  # Số lượng tiện ích giáo dục trong bán kính
    count_shopping = Column(Integer, default=0)   # Số lượng tiện ích mua sắm trong bán kính
    dist_shopping = Column(Numeric(10, 2))        # Khoảng cách đến mua sắm gần nhất (mét)
    dist_transportation = Column(Numeric(10, 2))  # Khoảng cách đến giao thông công cộng (mét)
    count_transportation = Column(Integer, default=0) # Số lượng tiện ích giao thông trong bán kính
    dist_environment = Column(Numeric(10, 2))     # Khoảng cách đến công viên/không gian xanh (mét)
    count_environment = Column(Integer, default=0) # Số lượng tiện ích xanh trong bán kính
    count_entertainment = Column(Integer, default=0) # Số lượng tiện ích giải trí trong bán kính
    dist_entertainment = Column(Numeric(10, 2))   # Khoảng cách đến giải trí gần nhất (mét)
    dist_safety = Column(Numeric(10, 2))          # Khoảng cách đến đồn công an/PCCC (mét)
    count_safety = Column(Integer, default=0)     # Số lượng tiện ích đồn công an/PCCC trong bán kính

    # --- ĐIỂM THÀNH PHẦN ĐÃ CHUẨN HÓA (0-100) ---
    score_healthcare = Column(Numeric(5, 2), default=0)
    score_education = Column(Numeric(5, 2), default=0)
    score_shopping = Column(Numeric(5, 2), default=0)
    score_transportation = Column(Numeric(5, 2), default=0)
    score_environment = Column(Numeric(5, 2), default=0)
    score_entertainment = Column(Numeric(5, 2), default=0)
    score_safety = Column(Numeric(5, 2), default=0)
