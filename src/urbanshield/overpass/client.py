import time, requests
from ..config import OVERPASS_PRIMARY, OVERPASS_FALLBACK, NOMINATIM_UA

HEADERS = {"User-Agent": NOMINATIM_UA}

def overpass_json(query, retries=3, sleep_s=5):
    urls = [OVERPASS_PRIMARY, OVERPASS_FALLBACK]
    last = None
    for attempt in range(retries):
        for url in urls:
            try:
                r = requests.post(url, data={"data": query}, headers=HEADERS, timeout=120)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last = e
                time.sleep(sleep_s)
    raise last

def fetch_by_poly(geom, table_key):
    from .queries import build_query
    q = build_query(geom, table_key)
    return overpass_json(q)
