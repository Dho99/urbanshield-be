import json
import time
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import RISK_LAYER_CACHE_TTL
from app.services.seed import get_mock_risk_layer, get_mock_districts, MOCK_RISK_LAYER, MOCK_DISTRICTS
from app.models.geo import Area, AreaBoundary
from app.models.prediction import RiskPrediction
from app.models.recommendation import Recommendation
from app.models.prediction import PredictionFactor

_cache = {"data": None, "ts": 0}


def _district_from_db(area: Area, pred: RiskPrediction | None, factors: list, reco: Recommendation | None) -> dict | None:
    if not pred:
        return None
    mock_district = next((d for d in get_mock_districts() if d.get("districtId") == area.slug), None)
    hist_events = mock_district.get("historicalEvents", []) if mock_district else []
    return {
        "districtId": area.slug,
        "district": area.name,
        "riskLevel": pred.risk_level,
        "score": int(pred.risk_score),
        "confidence": int(pred.confidence),
        "factors": [{"factor": f.feature, "contribution": int(f.contribution), "value": f.value} for f in factors],
        "recommendation": reco.action if reco and reco.action else "",
        "historicalEvents": hist_events,
    }


def get_risk_layer(db: Session | None = None):
    if db is not None:
        try:
            cached = _cache.get("data")
            now = time.time()
            if cached and now - _cache["ts"] < RISK_LAYER_CACHE_TTL:
                pass
            else:
                rows = (
                    db.query(Area, AreaBoundary, RiskPrediction)
                    .join(AreaBoundary, AreaBoundary.area_id == Area.id)
                    .join(RiskPrediction, RiskPrediction.area_id == Area.id)
                    .filter(RiskPrediction.scenario == "current")
                    .all()
                )
                if rows:
                    features = []
                    for area, boundary, pred in rows:
                        gj = db.execute(text("SELECT ST_AsGeoJSON(geom) FROM area_boundaries WHERE area_id = :aid"), {"aid": area.id}).scalar()
                        if not gj:
                            continue
                        geom = json.loads(gj)
                        features.append(
                            {
                                "type": "Feature",
                                "properties": {"districtId": area.slug, "district": area.name, "riskLevel": pred.risk_level, "score": int(pred.risk_score)},
                                "geometry": geom,
                            }
                        )
                    if features:
                        _cache["data"] = {"type": "FeatureCollection", "features": features}
                        _cache["ts"] = now
                        return _cache["data"]
        except Exception:
            pass
    return get_mock_risk_layer()


def get_district(district_id: str, db: Session | None = None):
    if db is not None:
        try:
            area = db.query(Area).filter(Area.slug == district_id).first()
            if area:
                pred = db.query(RiskPrediction).filter(RiskPrediction.area_id == area.id, RiskPrediction.scenario == "current").first()
                if pred:
                    factors = db.query(PredictionFactor).filter(PredictionFactor.prediction_id == pred.id).all()
                    reco = db.query(Recommendation).filter(Recommendation.area_id == area.id).first()
                    built = _district_from_db(area, pred, factors, reco)
                    if built:
                        return built
        except Exception:
            pass
    return next((d for d in get_mock_districts() if d["districtId"] == district_id), None)


def list_districts(db: Session | None = None) -> list[dict]:
    if db is not None:
        try:
            areas = db.query(Area).all()
            if areas:
                out = []
                for area in areas:
                    pred = db.query(RiskPrediction).filter(RiskPrediction.area_id == area.id, RiskPrediction.scenario == "current").first()
                    if not pred:
                        continue
                    factors = db.query(PredictionFactor).filter(PredictionFactor.prediction_id == pred.id).all()
                    reco = db.query(Recommendation).filter(Recommendation.area_id == area.id).first()
                    built = _district_from_db(area, pred, factors, reco)
                    if built:
                        out.append(built)
                if out:
                    return out
        except Exception:
            pass
    return get_mock_districts()
