from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.geo import Area
from app.models.recommendation import Recommendation
from app.schemas.recommendation import MitigationDecisionOut
from app.services import recommendation_service, map_service

router = APIRouter()


@router.get("", summary="Mitigation priority queue")
def list_all(
    risk: str | None = Query(default=None),
    q: str | None = Query(default=None, alias="q"),
    db: Session = Depends(get_db),
):
    try:
        rows = db.query(Recommendation).join(Area, Recommendation.area_id == Area.id).all()
        if rows:
            out = []
            for r in rows:
                area = db.query(Area).filter(Area.id == r.area_id).first()
                out.append({"areaId": area.slug if area else str(r.area_id), "area": area.name if area else str(r.area_id), "risk": "high" if r.estimated_impact == "High" else "low" if r.estimated_impact == "Low" else "medium", "priority": r.priority, "action": r.action, "estimatedImpact": r.estimated_impact, "reason": r.reason})
            if risk and risk != "all":
                out = [x for x in out if x["risk"] == risk]
            if q:
                out = [x for x in out if q.lower() in x["area"].lower()]
            out.sort(key=lambda x: x["priority"])
            if out:
                return out
    except Exception:
        pass
    return recommendation_service.list_recommendations(risk=risk, q=q)


@router.get("/{area_id}/decision", response_model=MitigationDecisionOut, summary="AI mitigation decision with evidence")
def decision_for_area(area_id: str, scenario: str = Query(default="current"), db: Session = Depends(get_db)):
    from app.ml.predictor import predict_for_district

    res = predict_for_district(area_id, scenario, db)
    if not res or not res.get("decision"):
        raise HTTPException(status_code=404, detail="Area not found")
    return res["decision"]


@router.get("/{area_id}", summary="Recommendation for area")
def by_area(area_id: str, db: Session = Depends(get_db)):
    try:
        area = db.query(Area).filter(Area.slug == area_id).first()
        if area:
            r = db.query(Recommendation).filter(Recommendation.area_id == area.id).first()
            if r:
                return {"areaId": area.slug, "area": area.name, "risk": "high" if r.estimated_impact == "High" else "low" if r.estimated_impact == "Low" else "medium", "priority": r.priority, "action": r.action, "estimatedImpact": r.estimated_impact, "reason": r.reason}
    except Exception:
        pass
    r = recommendation_service.get_for_area(area_id)
    if r:
        return r
    d = map_service.get_district(area_id, db)
    if not d:
        raise HTTPException(status_code=404, detail="Area not found")
    return recommendation_service.infer_for_district(d)
