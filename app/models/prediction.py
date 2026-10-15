from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from app.database.session import Base

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"
    id = Column(Integer, primary_key=True)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PredictionFactor(Base):
    __tablename__ = "prediction_factors"
    id = Column(Integer, primary_key=True)
    prediction_id = Column(Integer, ForeignKey("risk_predictions.id", ondelete="CASCADE"), nullable=False, index=True)
    feature = Column(String(100), nullable=False)
    contribution = Column(Float, nullable=False)
    value = Column(String(100))
    impact = Column(String(20))
