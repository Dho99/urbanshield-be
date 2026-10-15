import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.geo import Area, AreaBoundary
from app.models.prediction import RiskPrediction
from app.services import map_service
from app.services.seed import MOCK_DISTRICTS, MOCK_RISK_LAYER

router = APIRouter()


@router.get("", summary="List monitored areas")
def list_areas(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    live = map_service.list_districts(db)
    total = len(live)
    return {"items": live[offset : offset + limit], "total": total, "limit": limit, "offset": offset}


@router.get("/{area_id}", summary="Area with geometry and risk summary")
def get_area(area_id: str, db: Session = Depends(get_db)):
    d = map_service.get_district(area_id, db)
    if d:
        geom = None
        try:
            area = db.query(Area).filter(Area.slug == area_id).first()
            if area:
                gj = db.execute(text("SELECT ST_AsGeoJSON(geom) FROM area_boundaries WHERE area_id = :aid"), {"aid": area.id}).scalar()
                if gj:
                    geom = json.loads(gj)
        except Exception:
            pass
        if geom is None:
            geom = next((f["geometry"] for f in MOCK_RISK_LAYER["features"] if f["properties"]["districtId"] == area_id), None)
        return {"slug": d["districtId"], "name": d["district"], "admin_level": 8, "parent_region": "Kota Bandung", "geometry": geom, "risk_summary": {"risk_level": d["riskLevel"], "risk_score": d["score"], "confidence": d["confidence"]}}
    raise HTTPException(status_code=404, detail="Area not found")
