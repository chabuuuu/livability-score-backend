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
    dist_healthcare = Column(Numeric(10, 2))
    dist_education = Column(Numeric(10, 2))
    count_shopping = Column(Integer, default=0)
    dist_transportation = Column(Numeric(10, 2))
    dist_environment = Column(Numeric(10, 2))
    count_entertainment = Column(Integer, default=0)
    dist_safety = Column(Numeric(10, 2))

    # --- Normalized Scores ---
    score_healthcare = Column(Numeric(5, 2), default=0)
    score_education = Column(Numeric(5, 2), default=0)
    score_shopping = Column(Numeric(5, 2), default=0)
    score_transportation = Column(Numeric(5, 2), default=0)
    score_environment = Column(Numeric(5, 2), default=0)
    score_entertainment = Column(Numeric(5, 2), default=0)
    score_safety = Column(Numeric(5, 2), default=0)
    
    # --- Timestamps ---
    # Lưu ý: Tên cột trong SQL của bạn là create_at/update_at (không có 'd')
    create_at = Column(DateTime(timezone=True), server_default=func.now())
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    delete_at = Column(DateTime(timezone=True), nullable=True)