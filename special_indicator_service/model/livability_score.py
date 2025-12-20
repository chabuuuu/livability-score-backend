from sqlalchemy import Column, BigInteger, Numeric, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Nếu bạn có file base chung thì import, không thì khai báo tại đây
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class PropertyLivabilityScore(Base):
    __tablename__ = "property_livability_scores"

    id = Column(BigInteger, primary_key=True, index=True)
    property_id = Column(BigInteger, unique=True, nullable=False)
    
    # --- Raw Metrics (Chỉ số thô từ khoảng cách/số lượng) ---
    dist_healthcare = Column(Numeric(10, 2))
    dist_education = Column(Numeric(10, 2))
    count_shopping = Column(Integer, default=0)
    dist_transportation = Column(Numeric(10, 2))
    dist_environment = Column(Numeric(10, 2))
    count_entertainment = Column(Integer, default=0)
    dist_safety = Column(Numeric(10, 2))

    # --- Normalized Component Scores (Điểm thành phần 0-100) ---
    score_healthcare = Column(Numeric(5, 2), default=0)
    score_education = Column(Numeric(5, 2), default=0)
    score_shopping = Column(Numeric(5, 2), default=0)
    score_transportation = Column(Numeric(5, 2), default=0)
    score_environment = Column(Numeric(5, 2), default=0)
    score_entertainment = Column(Numeric(5, 2), default=0)
    score_safety = Column(Numeric(5, 2), default=0)
    
    # --- SPECIAL IMPACT SCORES (MỚI) ---
    # Các chỉ số này được cập nhật từ Service thu thập tin tức
    flood_impact_score = Column(Numeric(5, 2), default=0)    # Điểm trừ ngập lụt
    accident_impact_score = Column(Numeric(5, 2), default=0) # Điểm trừ tai nạn
    future_project_score = Column(Numeric(5, 2), default=0)  # Điểm cộng tiềm năng (Metro, cầu, đường...)

    # --- Metadata ---
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
