from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.database.session import Base

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    source = Column(String(100), nullable=False)
    description = Column(String(500))
    last_update = Column(DateTime(timezone=True), server_default=func.now())
    completeness = Column(Float)
    record_count = Column(Integer)
