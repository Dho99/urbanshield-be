# UrbanShield AI — Urban Flood Risk Intelligence

Explainable geospatial intelligence for urban flood risk prediction and mitigation prioritization. Monorepo with **FastAPI + PostGIS** backend and **Next.js 16 + MapLibre** frontend.

**Pilot:** Kota Bandung — 30 kecamatan (8 pilot subset), `urban_osm_features_final.csv` 30×26 OSM features + `kecamatan.geojson` boundaries.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI 0.115.6, SQLAlchemy 2.0, GeoAlchemy2, PostGIS 16, Alembic, Pydantic, XGBoost/LightGBM/SHAP, JWT (Better Auth compatible) |
| Frontend | Next.js 16.4 App Router, React 19, TypeScript, Tailwind 4, shadcn/ui, TanStack Query, Axios, Better Auth (sqlite), MapLibre GL, Recharts |
| Infra | Python 3.13 venv, Node, PostgreSQL 16 + PostGIS 3.4 (local `localhost:5432` or `docker-compose`), no virtualization required for local run |

## Ports

| Service | URL |
|---|---|
| Frontend | `http://localhost:3005` (`npm run dev -p 3005`) |
| Backend | `http://localhost:8000` — docs `http://localhost:8000/docs` · redoc `http://localhost:8000/redoc` · openapi `http://localhost:8000/openapi.json` |
| DB | `localhost:5432` db `urbanshield` user `postgres` |

CORS single source: `CORS_ORIGINS=http://localhost:3005` (backend) ↔ `BETTER_AUTH_URL=http://localhost:3005` (frontend). API `http://localhost:8000/api/v1`.

## Quickstart — Local (no Docker)

Requires: Python 3.13, Node 18+, PostgreSQL 16 + PostGIS 3.4 running at `localhost:5432`.

```bash
# 1. Backend
cd backend
python -m venv venv
.\venv\Scripts\activate        # Windows; source venv/bin/activate on Unix
pip install -r requirements.txt
copy .env.example .env        # ensure DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/urbanshield
psql -U postgres -c "CREATE DATABASE urbanshield;"
psql -U postgres -d urbanshield -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Alembic (optional — seed also does create_all)
# alembic revision --autogenerate -m "init"  # if no revision
alembic upgrade head

# Seed — 30 districts live (fallback mock 8 if DB down)
python -m scripts.seed --dry-run   # expect 30 features / 30 csv / overlap 8/8
python -m scripts.seed --reset     # upsert roles+users+datasets+areas+boundaries+features+predictions

# Start API
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Frontend (second terminal, project root)
cd frontend
npm install
copy .env.example .env.local
# .env.local: NEXT_PUBLIC_USE_MOCK=false to hit live backend; true for offline mock
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1, BETTER_AUTH_URL=http://localhost:3005
npm run dev    # http://localhost:3005
```

## Docker Alternative (optional)

```bash
cd backend
docker compose up --build              # waits for db healthy
docker compose --profile seed run --rm seed   # or: docker compose exec api python -m scripts.seed --reset
# frontend still runs locally: npm run dev at 3005 (api at 8000 via published port)
```

Seed inside compose uses `DATABASE_URL=postgresql+psycopg2://postgres:password@db:5432/urbanshield` (host `db`), local uses `localhost:5432`.

## Docs

- Backend API: `http://localhost:8000/docs` · source `backend/docs/api.md` · setup `backend/README.md` · PRD `backend/prd/prd_v1.md`
- Frontend integration: `frontend/docs/api.md` · setup `frontend/README.md` · PRD `frontend/prd/prd_v1.md`
- Setup/seed detail: `backend/README.md` (CRS 32748→4326, seed CLI, verify) + `backend/scripts/seed.py` header

## Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/        dashboard, map, prediction, recommendation, areas, datasets, auth
│   │   ├── core/       config, security (JWT HS256)
│   │   ├── models/     geo, prediction, recommendation, dataset, user
│   │   ├── services/   seed (mock), map_service, recommendation_service, dataset_service
│   │   ├── ml/         model_loader, predictor (XGBoost/LightGBM + multiplier fallback), explainer (SHAP)
│   │   └── main.py     FastAPI + CORS + logging
│   ├── scripts/seed.py  idempotent PostGIS seeder (--dry-run/--reset)
│   ├── urban_osm_crawler/output/  kecamatan.geojson + 30×26 CSV
│   └── alembic.ini / migrations/
└── frontend/
    ├── src/lib/api/     api-client (axios + Bearer + 401), services/{auth,area,map,prediction,recommendation,dataset}
    ├── src/hooks/queries.ts  useAreas/useRiskLayer/usePrediction/useDatasets etc
    ├── src/types/       Area/Dataset/GeoJSON/RiskLayer matching backend
    └── src/app/         (app)/dashboard, map, prediction, recommendation, datasets, profile + (auth)
```

## Scripts

| Location | Command | Purpose |
|---|---|---|
| backend | `venv\Scripts\python -m scripts.seed --reset` | Seed 30-district live |
| backend | `alembic upgrade head` | Apply migrations |
| backend | `uvicorn app.main:app --reload` | Dev API |
| frontend | `npm run dev` | Dev at 3005 |
| frontend | `npm run build` | 14 workers build |
| frontend | `npm run lint` | eslint |

## Env — canonical `.env.example`

Backend `backend/.env.example` (10 vars) — `DATABASE_URL`, `OVERPASS_*`, `NOMINATIM_UA`, `SECRET_KEY`, `CORS_ORIGINS=http://localhost:3005`, `JWT_ALGORITHM/EXPIRE`, `RISK_LAYER_CACHE_TTL`, `LOG_LEVEL`.
Frontend `frontend/.env.example` (5 vars) — `BETTER_AUTH_SECRET/URL=http://localhost:3005`, `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`, `NEXT_PUBLIC_USE_MOCK=false`, `AUTH_DB_PATH`.

## License

Internal pilot — not for production without secret rotation.
