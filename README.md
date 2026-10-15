# Backend — UrbanShield AI API

FastAPI + PostgreSQL 16 + PostGIS 3.4 · SQLAlchemy 2.0 · GeoAlchemy2 · Alembic · JWT · XGBoost/LightGBM/SHAP.

## Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/urbanshield
# ensure Postgres 16 + PostGIS 3.4 running at localhost:5432 (no Docker required)
psql -U postgres -c "CREATE DATABASE urbanshield;"
psql -U postgres -d urbanshield -c "CREATE EXTENSION IF NOT EXISTS postgis;"
alembic upgrade head   # optional — seed also does Base.metadata.create_all
```

Env `.env.example` (10 vars): `DATABASE_URL`, `OVERPASS_PRIMARY/FALLBACK`, `NOMINATIM_UA`, `SECRET_KEY`, `CORS_ORIGINS=http://localhost:3005`, `JWT_ALGORITHM=HS256`, `JWT_EXPIRE_MINUTES=1440`, `RISK_LAYER_CACHE_TTL=60`, `LOG_LEVEL=INFO`. Copy to `.env`; production rotate `SECRET_KEY`.

## Seed

Sources `urban_osm_crawler/output/kecamatan.geojson` (30 districts) + `urban_osm_features_final.csv` (30×26) + `app/services/seed.py` (8 mock) + `app/services/dataset_service.py` (7 datasets).

```bash
python -m scripts.seed --dry-run   # geojson features 30, csv rows 30, overlap 8/8, roles 3 datasets 7
python -m scripts.seed             # upsert
python -m scripts.seed --reset     # TRUNCATE CASCADE RESTART IDENTITY + reseed
```

CRS note: `kecamatan.geojson` currently `EPSG::32748` (UTM 784824,9228817) — `scripts/seed.py` inserts via `WKTElement` / `ST_GeomFromGeoJSON`; adapt to `ST_Transform(ST_GeomFromGeoJSON, 4326)` when real OSM 32748 geojson is seeded to `GEOMETRY 4326`.

Targets: `roles(3) → users(admin@urbanshield.local/Admin123!) → datasets(7) → areas(30) + area_boundaries(MULTIPOLYGON 4326) → osm_features + weather_features + population_features → risk_predictions(30) + prediction_factors → recommendations(30)`.

Docker alt: `docker compose up --build` (db health `pg_isready`) → `docker compose --profile seed run --rm seed`.

## Set Origin (CORS)

Single source: `CORS_ORIGINS=http://localhost:3005` (must match frontend `BETTER_AUTH_URL` + `package.json dev -p 3005`). Code `app/core/config.py:20` default `3005`, `app/main.py:29` `CORSMiddleware allow_origins=CORS_ORIGINS allow_credentials True`. Frontend `src/lib/api/api-client.ts:8 withCredentials true` + `Authorization: Bearer urbanshield_token` (localStorage, cleared on 401 except `/login|/register|/api/auth`).

## Start

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# http://localhost:8000/docs  http://localhost:8000/redoc  http://localhost:8000/openapi.json
# health GET /health, GET /api/v1/health
```

Docker: `docker compose up` → `http://localhost:8000` (ports `5432:5432`, `8000:8000`).

OpenAPI metadata enriched: `servers: [{url: http://localhost:8000}, {url: http://localhost:8000/api/v1}]`, per-router `summary/description` + `Query(description)` in `app/api/*.py`, `Field(description, example)` in `app/schemas/*.py`.

## Test

Jalankan rangkaian pengujian otomatis lengkap (*Automated Test Suite*):

```bash
pytest tests/ -v
```

Rangkaian test mencakup:
- `tests/test_prediction.py`: Pengujian model ML XGBoost, feature vector 14 dimensi, 4 skenario simulasi, dan struktur SHAP explanations.
- `tests/test_api.py`: Pengujian seluruh endpoint FastAPI via `TestClient` (`/health`, `/dashboard/overview`, `/map/risk-layer`, `/predictions`, `/recommendations`, `/datasets`).
- Hasil: **14 / 14 passed (100%)**.

---

## Dokumentasi Teknis

- [Siklus Data Mining (CRISP-DM)](docs/DATA_MINING_LIFECYCLE.md): Laporan lengkap tahapan business understanding, pengumpulan data multi-modal, EDA, pemodelan, evaluasi baseline, dan XAI.
- [Evaluasi Model & Validasi Ground Truth](docs/model_evaluation_and_ground_truth.md): Perbandingan metrik model v2 vs baseline serta validasi terhadap titik banjir historis BPBD Kota Bandung.
- [Dokumentasi API](docs/api.md): Spesifikasi kontrak endpoint REST API.
- [Pipeline Machine Learning](ml_pipeline/README.md): Panduan reproduksi dataset dan pelatihan model.

---

## Project Structure

PRD `prd/prd_v1.md` — services auth/geo/prediction/explain/recommendation/datasets, DB `users, roles, areas, area_boundaries, risk_predictions, prediction_factors, recommendations, datasets, osm_features, weather_features, population_features`, structure `app/{api,core,models,schemas,services,ml,database,migrations}`.
