from sqlalchemy import Column, BigInteger, Numeric, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Nếu bạn có file base chung thì import, không thì khai báo tại đây
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class PropertyLivabilityScore(Base):
    __tablename__ = "property_livability_scores"

    id = Column(BigInteger, primary_key=True, index=True)
    property_id = Column(BigInteger, unique=True, nullable=False)
    
    # --- Raw Metrics ---
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

    # --- Normalized Scores ---
    score_healthcare = Column(Numeric(5, 2), default=0)
    score_education = Column(Numeric(5, 2), default=0)
    score_shopping = Column(Numeric(5, 2), default=0)
    score_transportation = Column(Numeric(5, 2), default=0)
    score_environment = Column(Numeric(5, 2), default=0)
    score_entertainment = Column(Numeric(5, 2), default=0)
    score_safety = Column(Numeric(5, 2), default=0)
    
    # --- SPECIAL IMPACT SCORES ---
    # Các chỉ số này được cập nhật từ Service thu thập tin tức
    flood_impact_score = Column(Numeric(5, 2), default=0)    # Điểm trừ ngập lụt
    accident_impact_score = Column(Numeric(5, 2), default=0) # Điểm trừ tai nạn
    future_project_score = Column(Numeric(5, 2), default=0)  # Điểm cộng tiềm năng (Metro, cầu, đường...)


    # --- Timestamps ---
    # Lưu ý: Tên cột trong SQL của bạn là create_at/update_at (không có 'd')
    create_at = Column(DateTime(timezone=True), server_default=func.now())
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    delete_at = Column(DateTime(timezone=True), nullable=True)