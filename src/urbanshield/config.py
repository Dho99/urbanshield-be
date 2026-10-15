import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
BOUNDARY_DIR = DATA_DIR / "boundaries"

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/urbanshield")
OVERPASS_PRIMARY = os.getenv("OVERPASS_PRIMARY", "https://overpass-api.de/api/interpreter")
OVERPASS_FALLBACK = os.getenv("OVERPASS_FALLBACK", "https://overpass.kumi.systems/api/interpreter")
NOMINATIM_UA = os.getenv("NOMINATIM_UA", "urbanshield-ai/1.0")

for d in [RAW_DIR, PROCESSED_DIR, BOUNDARY_DIR]:
    d.mkdir(parents=True, exist_ok=True)
