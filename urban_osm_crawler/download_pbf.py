import urllib.request
from pathlib import Path
from tqdm import tqdm

RAW_DIR = Path(__file__).resolve().parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PBF_FILE = RAW_DIR / "java-latest.osm.pbf"

# Geofabrik Indonesia / Java PBF link (~75MB)
URL = "https://download.geofabrik.de/asia/indonesia/java-latest.osm.pbf"

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def ensure_pbf():
    if PBF_FILE.exists() and PBF_FILE.stat().st_size > 10_000_000:
        print(f"PBF file already exists: {PBF_FILE} ({PBF_FILE.stat().st_size / 1e6:.1f} MB)")
        return PBF_FILE
    
    print(f"Downloading PBF from {URL} ...")
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=URL.split('/')[-1]) as t:
        urllib.request.urlretrieve(URL, filename=PBF_FILE, reporthook=t.update_to)
    print(f"Saved PBF: {PBF_FILE}")
    return PBF_FILE

if __name__ == "__main__":
    ensure_pbf()
