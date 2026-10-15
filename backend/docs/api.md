# UrbanShield API — Reference

Base `http://localhost:8000/api/v1` — Swagger `http://localhost:8000/docs` · ReDoc `http://localhost:8000/redoc` · JSON `http://localhost:8000/openapi.json`. Errors `{"detail": str}`.

## Endpoints

| Method | Path | Auth | Summary |
|---|---|---|---|
| GET | `/health` · `/api/v1/health` | none | `{"status":"ok"}` |
| POST | `/api/v1/auth/register` | none | `UserCreate → UserOut` |
| POST | `/api/v1/auth/login` | none | `LoginRequest → Token{bearer}` |
| GET | `/api/v1/auth/me` | optional Bearer → 401 | Current user |
| GET | `/api/v1/dashboard/overview` | none (db) | `RiskOverviewOut` counts high/med/low |
| GET | `/api/v1/map/risk-layer` | none | GeoJSON `FeatureCollection` (cache 60s) |
| GET | `/api/v1/map/districts/{district_id}` | none | `DistrictRiskOut` · 404 |
| GET | `/api/v1/prediction/districts` · `/predictions/districts` | none | `DistrictRiskOut[]` |
| POST | `/api/v1/prediction/predict` · `/predictions/predict` · `POST /prediction` · `POST /predictions` | none | `PredictionRequest → RiskPredictionOut` (multiplier fallback) |
| GET | `/api/v1/prediction/{id}/explanation` · `/predictions/{id}/explanation` | none | `?districtId&scenario → ExplanationOut` (SHAP if model.pkl else positive) |
| GET | `/api/v1/recommendations` · `/recommendation` | none | `?risk=all|high|med|low&q= → RecommendationOut[]` |
| GET | `/api/v1/recommendations/{area_id}` · `/recommendation/{area_id}` | none | `RecommendationDetailOut` · 404 |
| GET | `/api/v1/areas?limit&offset` | none | `{items:DistrictRisk[], total, limit, offset}` paginated |
| GET | `/api/v1/areas/{area_id}` | none | `{slug, name, admin_level, parent_region, geometry, risk_summary}` · `ST_AsGeoJSON` · 404 |
| GET | `/api/v1/datasets?source` | none | `DatasetOut[]` · `?source=OSM|BNPB|BMKG|BPS|DEM` |

## Schemas

- `UserCreate {email:EmailStr, password, full_name?, role=viewer}` ROLE_MAP `admin→admin, analyst|city_planner|disaster_response|researcher→analyst, policy_analyst|viewer→viewer`; `UserOut {id,email,full_name,role,is_active}`; `Token {access_token, token_type=bearer}` HS256 `JWT_EXPIRE_MINUTES 1440`.
- `PredictionRequest {districtId, scenario: current|heavy_rain_24h|heavy_rain_72h|drainage_failure, date?}`; `DistrictRiskOut {districtId,district,riskLevel,score,confidence,factors[{factor,contribution,value}],recommendation}`; `RiskPredictionOut + {scenario label, predictedAt ISO}`; `ExplanationOut {prediction_id, main_factors[{feature,contribution,value,impact positive|negative}]}`; `RiskOverviewOut {totalMonitored,highRisk,mediumRisk,lowRisk,updatedAt ISO}`.
- `AreaOut/AreaDetailOut/RiskLayerOut FeatureCollection Polygon {districtId,district,riskLevel,score}`; `RecommendationOut {areaId,area,risk,priority,action,estimatedImpact,reason}`; `DatasetOut {id,name,source,description,last_update ISO,completeness,record_count}` (7: OSM 1240/0.92, Roads 5820/0.95, Boundaries 30/1.0, BNPB 86/0.78, BMKG 365/0.85, BPS 30/0.88, DEM 30/0.9).

## Behavior

- All non-`auth/me` public; `require_role` unused (viewer/analyst/admin not enforced).
- DB→mock fallback: each router tries `Session → Area/RiskPrediction` else `MOCK_DISTRICTS 8` / `MOCK_RISK_LAYER` / `MOCK_RECOMMENDATIONS 6` / `DATASETS 7`; risks always `high≥70 medium≥40 low`.
- Scenario multipliers (no model.pkl): `current 1.0, heavy_rain_24h 1.12, 72h 1.25, drainage_failure 1.18` clamp 100; ML `app/ml/artifacts/model.pkl` + `shap.Explainer` if present.
- Pagination: `GET /areas` `limit 1-100 default 50, offset ≥0`.
- Duplicate mounts intentional: `/prediction` canonical frontend `NEXT_PUBLIC_API_URL=/api/v1/prediction/*` vs `/predictions` PRD plural.

## Errors

`422` validation, `400 Email already registered`, `401 Invalid credentials|Not authenticated`, `403 Insufficient role`, `404 District/Area not found`. Normalize `detail||message`.

## Env

`DATABASE_URL localhost:5432` (compose `db:5432`), `CORS_ORIGINS=http://localhost:3005`, `SECRET_KEY`, `JWT_ALGORITHM/EXPIRE`, `RISK_LAYER_CACHE_TTL=60`, `LOG_LEVEL`.
