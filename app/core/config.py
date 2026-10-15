import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

def _normalize_db_url(url: str) -> str:
    # Neon .env uses postgresql:// ; SQLAlchemy needs postgresql+psycopg2://
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


DATABASE_URL = _normalize_db_url(
    os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:password@localhost:5432/urbanshield",
    )
)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

OVERPASS_PRIMARY = os.getenv(
    "OVERPASS_PRIMARY", "https://overpass-api.de/api/interpreter")
OVERPASS_FALLBACK = os.getenv(
    "OVERPASS_FALLBACK", "https://overpass.kumi.systems/api/interpreter")
NOMINATIM_UA = os.getenv("NOMINATIM_UA", "urbanshield-ai/1.0")

CORS_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS", "http://localhost:3005").split(",") if o.strip()]
API_PREFIX = "/api/v1"
RISK_LAYER_CACHE_TTL = int(os.getenv("RISK_LAYER_CACHE_TTL", "60"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
