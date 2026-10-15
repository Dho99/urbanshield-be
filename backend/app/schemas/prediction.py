from pydantic import BaseModel
from typing import Literal

class FactorOut(BaseModel):
    factor: str
    contribution: float
    value: str

class PredictionRequest(BaseModel):
    districtId: str
    scenario: Literal["current", "heavy_rain_24h", "heavy_rain_72h", "drainage_failure"] = "current"
    date: str | None = None

class DistrictRiskOut(BaseModel):
    districtId: str
    district: str
    riskLevel: Literal["low", "medium", "high"]
    score: int
    confidence: int
    factors: list[FactorOut]
    recommendation: str

class RiskPredictionOut(DistrictRiskOut):
    scenario: str
    predictedAt: str
    decision: dict | None = None

class ExplanationFactor(BaseModel):
    feature: str
    contribution: float
    value: str
    impact: str

class ExplanationOut(BaseModel):
    prediction_id: int
    main_factors: list[ExplanationFactor]

class RiskOverviewOut(BaseModel):
    totalMonitored: int
    highRisk: int
    mediumRisk: int
    lowRisk: int
    updatedAt: str
