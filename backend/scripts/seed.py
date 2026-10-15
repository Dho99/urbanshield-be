"""
Idempotent PostGIS seeder for UrbanShield AI.

Sources:
  urban_osm_crawler/output/kecamatan.geojson  (30 districts, Polygon 4326)
  urban_osm_crawler/output/urban_osm_features_final.csv  (30 x 26 cols, seed 42)
  app/services/seed.py  (MOCK_DISTRICTS 8, recommendations, scenario logic)
  app/services/dataset_service.py  (7 datasets)

Targets (ORM tables via app.database.session.Base):
  roles, users, datasets, areas, area_boundaries, osm_features,
  weather_features, population_features, risk_predictions,
  prediction_factors, recommendations

Usage:
  python -m scripts.seed              # upsert safe
  python -m scripts.seed --reset      # truncate + reseed
  python -m scripts.seed --dry-run    # print counts, no DB

Inside docker:
  docker compose exec api python -m scripts.seed --reset
"""
import argparse
import csv
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import Base, engine, SessionLocal
from app.models.user import Role, User
from app.models.geo import Area, AreaBoundary, OsmFeature, WeatherFeature, PopulationFeature
from app.models.prediction import RiskPrediction, PredictionFactor
from app.models.recommendation import Recommendation
from app.models.dataset import Dataset
from app.core.security import hash_password
from app.services.mitigation_engine import build_decision
from app.services.seed import MOCK_DISTRICTS, MOCK_RECOMMENDATIONS, risk_level
from app.services.dataset_service import DATASETS

GEOJSON_PATH = BACKEND_DIR / "urban_osm_crawler" / "output" / "kecamatan.geojson"
CSV_PATH = BACKEND_DIR / "urban_osm_crawler" / "output" / "urban_osm_features_final.csv"

SEED_ADMIN_EMAIL = "admin@urbanshield.local"
SEED_ADMIN_PASSWORD = "Admin123!"
SEED_ADMIN_NAME = "Admin"

DERIVED_TEMPLATES = [
    {"action": "Routine monitoring", "reason": "Stable", "impact": "Low"},
    {"action": "Drain desilting program", "reason": "Seasonal siltation", "impact": "Medium"},
    {"action": "Riverbank monitoring", "reason": "Catchment buffer", "impact": "Medium"},
    {"action": "Pump station maintenance", "reason": "Capacity check", "impact": "Medium"},
    {"action": "Drainage improvement", "reason": "Low drainage density", "impact": "High"},
    {"action": "Retention pond construction", "reason": "Low-lying blocks", "impact": "High"},
]


def slugify(name: str) -> str:
    return name.strip().lower().replace(" ", "-")


def ensure_postgis(db: Session):
    db.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    db.commit()


def seed_roles(db: Session):
    for name in ["admin", "analyst", "viewer"]:
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name))
    db.commit()


def seed_admin(db: Session):
    ensure_roles = db.query(Role).filter(Role.name == "admin").first()
    if not ensure_roles:
        seed_roles(db)
        ensure_roles = db.query(Role).filter(Role.name == "admin").first()
    if db.query(User).filter(User.email == SEED_ADMIN_EMAIL).first():
        return
    admin = User(email=SEED_ADMIN_EMAIL, hashed_password=hash_password(SEED_ADMIN_PASSWORD), full_name=SEED_ADMIN_NAME, role_id=ensure_roles.id, is_active=True)
    db.add(admin)
    db.commit()


def seed_datasets(db: Session):
    for row in DATASETS:
        existing = db.query(Dataset).filter(Dataset.name == row["name"]).first()
        if existing:
            existing.source = row["source"]
            existing.description = row["description"]
            existing.completeness = row["completeness"]
            existing.record_count = row["record_count"]
        else:
            db.add(Dataset(name=row["name"], source=row["source"], description=row["description"], completeness=row["completeness"], record_count=row["record_count"]))
    db.commit()


def load_geojson():
    if not GEOJSON_PATH.exists():
        print(f"[seed] geojson missing: {GEOJSON_PATH}", file=sys.stderr)
        return []
    data = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    return data.get("features", [])


def load_csv():
    if not CSV_PATH.exists():
        print(f"[seed] csv missing: {CSV_PATH}", file=sys.stderr)
        return {}
    rows = {}
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["district"]] = r
    return rows


def derive_score(row: dict) -> int:
    try:
        wd = float(row.get("water_density", 0) or 0) * 10000
        rd = float(row.get("road_density", 0) or 0)
        fd = float(row.get("facility_density", 0) or 0)
        bd = float(row.get("building_density", 0) or 0) / 100
        raw = 22 + wd * 1.5 + rd * 1.2 + fd * 0.9 + bd * 0.8
        return max(18, min(84, round(raw)))
    except Exception:
        return 42


def seed_areas_and_boundaries(db: Session, features: list[dict]) -> dict[str, Area]:
    slug_to_area: dict[str, Area] = {}
    for feat in features:
        props = feat.get("properties", {})
        name = props.get("name") or props.get("district") or "Unknown"
        slug = slugify(name)
        geom = feat.get("geometry")
        if not geom:
            continue
        area = db.query(Area).filter(Area.slug == slug).first()
        if not area:
            area = Area(slug=slug, name=name, admin_level=8, parent_region="Kota Bandung", osm_id=props.get("osm_id"))
            db.add(area)
            db.flush()
        else:
            area.name = name
            area.admin_level = 8
            area.parent_region = "Kota Bandung"
            if props.get("osm_id") is not None:
                area.osm_id = props.get("osm_id")
        slug_to_area[slug] = area
        geom_json = json.dumps(geom)
        existing_boundary = db.query(AreaBoundary).filter(AreaBoundary.area_id == area.id).first()
        if existing_boundary:
            db.execute(text("UPDATE area_boundaries SET geom = ST_GeomFromGeoJSON(:gj) WHERE area_id = :aid"), {"gj": geom_json, "aid": area.id})
        else:
            db.execute(text("INSERT INTO area_boundaries (area_id, geom) VALUES (:aid, ST_GeomFromGeoJSON(:gj))"), {"aid": area.id, "gj": geom_json})
    db.commit()
    return slug_to_area


def seed_osm_and_features(db: Session, slug_to_area: dict[str, Area], csv_rows: dict):
    for slug, area in slug_to_area.items():
        name = area.name
        row = csv_rows.get(name)
        if not row:
            continue
        db.query(OsmFeature).filter(OsmFeature.area_id == area.id).delete()
        db.query(WeatherFeature).filter(WeatherFeature.area_id == area.id).delete()
        db.query(PopulationFeature).filter(PopulationFeature.area_id == area.id).delete()
        try:
            geom_wkt = db.execute(text("SELECT ST_AsText(geom) FROM area_boundaries WHERE area_id = :aid"), {"aid": area.id}).scalar()
        except Exception:
            geom_wkt = None
        if not geom_wkt:
            geom_wkt = "POINT(107.61 -6.90)"
        tags = {k: v for k, v in row.items() if k not in ("district",)}
        from geoalchemy2.elements import WKTElement

        db.add(OsmFeature(osm_type="relation", category="aggregated", name=name, tags=tags, area_id=area.id, extra={"source": "urban_osm_features_final.csv"}, geom=WKTElement(geom_wkt, srid=4326)))
        try:
            water_density = float(row.get("water_density", 0) or 0)
            rainfall = round(40 + water_density * 80000 + (hash(name) % 20), 1)
        except Exception:
            rainfall = 60.0
        db.add(WeatherFeature(area_id=area.id, rainfall_mm=rainfall))
        try:
            bd = float(row.get("building_density", 0) or 0) * 10
            pop = round(5000 + bd * 8, 1)
        except Exception:
            pop = 8000.0
        db.add(PopulationFeature(area_id=area.id, population_density=pop, source="BPS-proxy"))
    db.commit()


def seed_predictions_and_recommendations(db: Session, slug_to_area: dict[str, Area], csv_rows: dict):
    mock_by_slug = {slugify(d["district"]): d for d in MOCK_DISTRICTS}
    mock_reco_by_id = {r["areaId"]: r for r in MOCK_RECOMMENDATIONS}
    for slug, area in slug_to_area.items():
        db.query(PredictionFactor).filter(PredictionFactor.prediction_id.in_(db.query(RiskPrediction.id).filter(RiskPrediction.area_id == area.id))).delete(synchronize_session=False)
        db.query(RiskPrediction).filter(RiskPrediction.area_id == area.id).delete()
        db.query(Recommendation).filter(Recommendation.area_id == area.id).delete()
    db.commit()

    for slug, area in slug_to_area.items():
        base = mock_by_slug.get(slug)
        row = csv_rows.get(area.name)
        decision = None
        if base:
            score = base["score"]
            level = base["riskLevel"]
            confidence = base["confidence"]
            factors = base["factors"]
            reco_text = base["recommendation"]
        else:
            score = derive_score(row) if row else 42
            level = risk_level(score)
            confidence = 78 + (hash(slug) % 12)
            wd = row.get("water_density", "") if row else ""
            rd = row.get("road_density", "") if row else ""
            bd = row.get("building_density", "") if row else ""
            fd = row.get("facility_density", "") if row else ""
            factors = [
                {"factor": "Rainfall intensity", "contribution": 28 + (hash(slug + "rain") % 10), "value": f"{45 + (hash(slug) % 90)} mm / 24h"},
                {"factor": "Drainage density", "contribution": 22 + (hash(slug + "drain") % 10), "value": f"{round(0.6 + (hash(slug) % 18) / 10, 1)} km / km²"},
                {"factor": "Elevation", "contribution": 22 + (hash(slug + "elev") % 8), "value": f"{700 + (hash(slug) % 120)} m"},
                {"factor": "Population density", "contribution": 18 + (hash(slug + "pop") % 8), "value": f"{round(5 + (hash(slug) % 90) / 10, 1)}k / km²"},
            ]
            total = sum(f["contribution"] for f in factors)
            for f in factors:
                f["contribution"] = round(f["contribution"] * 100 / total)
            diff = 100 - sum(f["contribution"] for f in factors)
            factors[0]["contribution"] += diff
            decision = build_decision(slug, area.name, score, level, confidence, factors)
            reco_text = decision["headline_action"] + " — " + decision["why_this_action"][0]["reason"] if decision["why_this_action"] else decision["headline_action"]
        pred = RiskPrediction(area_id=area.id, scenario="current", risk_score=float(score), risk_level=level, confidence=float(confidence))
        db.add(pred)
        db.flush()
        for f in factors:
            db.add(PredictionFactor(prediction_id=pred.id, feature=f["factor"], contribution=float(f["contribution"]), value=f["value"], impact="positive"))
        mr = mock_reco_by_id.get(slug)
        if mr:
            db.add(Recommendation(area_id=area.id, priority=mr["priority"], action=mr["action"], reason=mr["reason"], estimated_impact=mr["estimatedImpact"]))
        else:
            top_action = (decision["actions"][0] if decision and decision["actions"] else {"title": reco_text, "priority": "Medium", "reason": reco_text})
            priority = 1 + (hash(slug) % 8) if level == "high" else 7 + (hash(slug) % 24)
            db.add(Recommendation(area_id=area.id, priority=priority, action=top_action["title"], reason=top_action["reason"], estimated_impact=top_action["priority"]))
    db.commit()


def seed_all(reset: bool = False, dry_run: bool = False):
    features = load_geojson()
    csv_rows = load_csv()
    print(f"[seed] geojson features: {len(features)}  csv rows: {len(csv_rows)}")
    if dry_run:
        mock_slugs = {slugify(d['district']) for d in MOCK_DISTRICTS}
        geo_slugs = {slugify(f.get('properties', {}).get('name', '')) for f in features}
        print(f"[seed] dry-run: would seed {len(features)} areas, {len(csv_rows)} osm rows, {len(features)} predictions+recommendations")
        print(f"[seed] pilot overlap 8 in 30: {len(mock_slugs & geo_slugs)}/8")
        print(f"[seed] roles 3, datasets {len(DATASETS)}, users 1 (admin)")
        return
    Base.metadata.create_all(bind=engine)
    ensure_postgis(SessionLocal())
    db = SessionLocal()
    try:
        if reset:
            print("[seed] --reset: truncating seeded tables...")
            db.execute(text("TRUNCATE prediction_factors, risk_predictions, recommendations, population_features, weather_features, osm_features, area_boundaries, areas, datasets, users, roles RESTART IDENTITY CASCADE"))
            db.commit()
        seed_roles(db)
        seed_admin(db)
        seed_datasets(db)
        slug_to_area = seed_areas_and_boundaries(db, features)
        seed_osm_and_features(db, slug_to_area, csv_rows)
        seed_predictions_and_recommendations(db, slug_to_area, csv_rows)
        counts = {
            "areas": db.query(Area).count(),
            "boundaries": db.query(AreaBoundary).count(),
            "osm_features": db.query(OsmFeature).count(),
            "weather": db.query(WeatherFeature).count(),
            "population": db.query(PopulationFeature).count(),
            "predictions": db.query(RiskPrediction).count(),
            "factors": db.query(PredictionFactor).count(),
            "recommendations": db.query(Recommendation).count(),
            "datasets": db.query(Dataset).count(),
            "roles": db.query(Role).count(),
            "users": db.query(User).count(),
        }
        print("[seed] done:", ", ".join(f"{k}={v}" for k, v in counts.items()))
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UrbanShield seed")
    parser.add_argument("--reset", action="store_true", help="truncate seeded tables before seeding")
    parser.add_argument("--dry-run", action="store_true", help="print what would be seeded without DB writes")
    args = parser.parse_args()
    seed_all(reset=args.reset, dry_run=args.dry_run)
