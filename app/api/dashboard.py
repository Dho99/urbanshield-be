from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.prediction import RiskPrediction
from app.services.seed import MOCK_DISTRICTS, now_iso

router = APIRouter()


@router.get("/overview", summary="Risk overview", description="Aggregated risk counts for monitored areas.")
def overview(db: Session = Depends(get_db)):
    try:
        rows = db.query(RiskPrediction).filter(RiskPrediction.scenario == "current").all()
        if rows:
            return {
                "totalMonitored": len(rows),
                "highRisk": sum(1 for r in rows if r.risk_level == "high"),
                "mediumRisk": sum(1 for r in rows if r.risk_level == "medium"),
                "lowRisk": sum(1 for r in rows if r.risk_level == "low"),
                "updatedAt": now_iso(),
            }
    except Exception:
        pass
    return {
        "totalMonitored": len(MOCK_DISTRICTS),
        "highRisk": sum(1 for d in MOCK_DISTRICTS if d["riskLevel"] == "high"),
        "mediumRisk": sum(1 for d in MOCK_DISTRICTS if d["riskLevel"] == "medium"),
        "lowRisk": sum(1 for d in MOCK_DISTRICTS if d["riskLevel"] == "low"),
        "updatedAt": now_iso(),
    }
