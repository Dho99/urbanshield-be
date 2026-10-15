from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database.session import Base

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True)
    priority = Column(Integer, nullable=False)
    action = Column(String(255), nullable=False)
    reason = Column(String(500))
    estimated_impact = Column(String(20))
