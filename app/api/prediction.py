from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.prediction import PredictionRequest
from app.ml.predictor import predict_for_district
from app.ml.explainer import explain_prediction
from app.services.seed import MOCK_DISTRICTS
from app.services import map_service

router = APIRouter()


@router.get("/districts", summary="List districts with baseline risk")
def list_districts(db: Session = Depends(get_db)):
    from app.services import map_service as ms

    return ms.list_districts(db)


@router.post("/predict", summary="Run flood risk prediction (frontend contract)")
def predict(body: PredictionRequest, db: Session = Depends(get_db)):
    res = predict_for_district(body.districtId, body.scenario, db)
    if not res:
        raise HTTPException(status_code=404, detail="District not found")
    return res


@router.post("", summary="Run flood risk prediction (PRD POST /predictions)", include_in_schema=True)
def predict_root(body: PredictionRequest, db: Session = Depends(get_db)):
    res = predict_for_district(body.districtId, body.scenario, db)
    if not res:
        raise HTTPException(status_code=404, detail="District not found")
    return res


@router.get("/{prediction_id}/explanation", summary="SHAP explanation for prediction")
def explanation(prediction_id: int, districtId: str | None = None, scenario: str = "current", db: Session = Depends(get_db)):
    district = map_service.get_district(districtId, db) if districtId else None
    if not district:
        district = map_service.list_districts(db)[0] if map_service.list_districts(db) else MOCK_DISTRICTS[0]
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return explain_prediction(district, scenario)
