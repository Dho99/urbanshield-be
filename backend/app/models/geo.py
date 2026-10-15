from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, ForeignKey, func, JSON
from geoalchemy2 import Geometry
from app.database.session import Base

class Area(Base):
    __tablename__ = "areas"
    id = Column(Integer, primary_key=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    admin_level = Column(Integer)
    parent_region = Column(String(255))
    osm_id = Column(BigInteger)

class AreaBoundary(Base):
    __tablename__ = "area_boundaries"
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="CASCADE"), primary_key=True)
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)

class OsmFeature(Base):
    __tablename__ = "osm_features"
    id = Column(Integer, primary_key=True)
    osm_id = Column(BigInteger)
    osm_type = Column(String(20))
    category = Column(String(50), nullable=False)
    name = Column(String(255))
    tags = Column(JSON)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="SET NULL"))
    geom = Column(Geometry("GEOMETRY", srid=4326), nullable=False)
    extra = Column(JSON)

class WeatherFeature(Base):
    __tablename__ = "weather_features"
    id = Column(Integer, primary_key=True)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True)
    rainfall_mm = Column(Float)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

class PopulationFeature(Base):
    __tablename__ = "population_features"
    id = Column(Integer, primary_key=True)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True)
    population_density = Column(Float)
    source = Column(String(100))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
