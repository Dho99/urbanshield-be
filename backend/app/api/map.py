from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services import map_service

router = APIRouter()


@router.get("/risk-layer", summary="GeoJSON risk layer")
def risk_layer(db: Session = Depends(get_db)):
    return map_service.get_risk_layer(db)


@router.get("/districts/{district_id}", summary="District detail with risk")
def district_detail(district_id: str, db: Session = Depends(get_db)):
    d = map_service.get_district(district_id, db)
    if not d:
        raise HTTPException(status_code=404, detail="District not found")
    return d
