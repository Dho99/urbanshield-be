import os
from pathlib import Path

TARGET = "Kota Bandung, Jawa Barat, Indonesia"

# Global instances according to OSM Wiki Overpass documentation:
# - private.coffee: 4 servers, 20 cores, 256GB RAM, no rate limit
# - overpass-api.de: main FOSSGIS instance
# - maps.mail.ru: VK Maps mirror
OVERPASS_SERVERS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

METRIC_CRS = "EPSG:32748"  # UTM zone 48S (Jawa Barat / Bandung)

MAX_RETRIES = 2
BACKOFF_SECONDS = 3
PAUSE_ON_ERROR = 30  # OSM wiki policy: wait 30s on 429/406/504
TIMEOUT = 60

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
