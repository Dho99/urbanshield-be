import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import CORS_ORIGINS, API_PREFIX, LOG_LEVEL
from app.api import dashboard as dashboard_api
from app.api import map as map_api
from app.api import prediction as prediction_api
from app.api import recommendation as recommendation_api
from app.api import areas as areas_api
from app.api import datasets as datasets_api
from app.api import auth as auth_api

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("urbanshield")

app = FastAPI(
    title="UrbanShield AI API",
    description=(
        "Explainable Geospatial Intelligence System for Urban Flood Risk Prediction and Mitigation Prioritization. "
        "PRD v1 services: auth (admin/analyst/viewer), geo, prediction (XGBoost/LightGBM+multiplier fallback), "
        "explain (SHAP), recommendation, datasets. Auth: Better Auth compatible JWT HS256 (optional for pilot). "
        "Docs: `GET /docs` Swagger, `/redoc`, `/openapi.json`. Frontend `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    servers=[{"url": "http://localhost:8000", "description": "Local dev"}, {"url": "http://localhost:8000/api/v1", "description": "API prefix"}],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    dur = (time.time() - start) * 1000
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} {dur:.1f}ms")
    return response

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

@app.get(f"{API_PREFIX}/health", tags=["health"])
def health_v1():
    return {"status": "ok"}

app.include_router(auth_api.router, prefix=f"{API_PREFIX}/auth", tags=["auth"])
app.include_router(dashboard_api.router, prefix=f"{API_PREFIX}/dashboard", tags=["dashboard"])
app.include_router(map_api.router, prefix=f"{API_PREFIX}/map", tags=["map"])
app.include_router(prediction_api.router, prefix=f"{API_PREFIX}/prediction", tags=["prediction"])
app.include_router(prediction_api.router, prefix=f"{API_PREFIX}/predictions", tags=["predictions"])
app.include_router(recommendation_api.router, prefix=f"{API_PREFIX}/recommendations", tags=["recommendations"])
app.include_router(recommendation_api.router, prefix=f"{API_PREFIX}/recommendation", tags=["recommendations"])
app.include_router(areas_api.router, prefix=f"{API_PREFIX}/areas", tags=["areas"])
app.include_router(datasets_api.router, prefix=f"{API_PREFIX}/datasets", tags=["datasets"])
