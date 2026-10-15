from pydantic import BaseModel
from typing import Literal

class RecommendationOut(BaseModel):
    areaId: str
    area: str
    risk: Literal["low", "medium", "high"]
    priority: int
    action: str
    estimatedImpact: str

class RecommendationDetailOut(RecommendationOut):
    reason: str | None = None

class DecisionWhy(BaseModel):
    factor: str
    contribution: float
    reason: str

class DecisionEvidence(BaseModel):
    factor: str
    value: str
    contribution: float

class DecisionAction(BaseModel):
    title: str
    priority: Literal["High", "Medium", "Low"]
    reason: str

class DecisionRiskSummary(BaseModel):
    districtId: str
    district: str
    score: int
    level: Literal["low", "medium", "high"]
    confidence: int

class MitigationDecisionOut(BaseModel):
    districtId: str
    district: str
    risk_summary: DecisionRiskSummary
    why_this_action: list[DecisionWhy]
    supporting_data: list[DecisionEvidence]
    actions: list[DecisionAction]
    headline_action: str
