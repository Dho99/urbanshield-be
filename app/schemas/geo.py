from pydantic import BaseModel
from typing import Any

class AreaOut(BaseModel):
    id: int
    slug: str
    name: str
    admin_level: int | None
    parent_region: str | None
    class Config:
        from_attributes = True

class AreaDetailOut(AreaOut):
    geometry: dict[str, Any] | None = None
    risk_summary: dict[str, Any] | None = None

class RiskLayerFeature(BaseModel):
    type: str = "Feature"
    properties: dict[str, Any]
    geometry: dict[str, Any]

class RiskLayerOut(BaseModel):
    type: str = "FeatureCollection"
    features: list[RiskLayerFeature]
