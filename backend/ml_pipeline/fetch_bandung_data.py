"""
fetch_bandung_data.py
Menarik data curah hujan harian (ERA5 via Open-Meteo) dan elevasi + kemiringan
untuk 30 kecamatan resmi Kota Bandung. Jalankan di komputer Anda (butuh internet).

    pip install requests pandas
    python fetch_bandung_data.py

Output (folder ./data_raw):
    rainfall_daily_2021_2023.csv   -> curah hujan harian per kecamatan
    rainfall_features.csv          -> ringkasan tahunan (total, maks 1 hari, maks 3 hari, hari >50 mm)
    terrain_features.csv           -> elevation_mean_m, slope_mean_deg

CATATAN:
- Koordinat di bawah adalah PERKIRAAN titik tengah (akurasi kira-kira 1-2 km).
  Jika CSV OSM Anda punya kolom lat/lon centroid, ganti dengan itu (lihat load_centroids()).
- Open-Meteo gratis untuk non-komersial. Cantumkan sumber di laporan:
  "Open-Meteo.com (ERA5 reanalysis, Copernicus/ECMWF)".
- Resolusi ERA5 kasar (~9-25 km), sehingga variasi antar kecamatan kecil.
"""
import os
import time
import requests
import pandas as pd

OUT = os.path.join(os.path.dirname(__file__), "data_raw")
os.makedirs(OUT, exist_ok=True)

START, END = "2021-01-01", "2023-12-31"

# 30 kecamatan resmi Kota Bandung (lat, lon perkiraan)
DISTRICTS = {
    "Andir": (-6.9125, 107.5800),
    "Antapani": (-6.9145, 107.6600),
    "Arcamanik": (-6.9300, 107.6850),
    "Astana Anyar": (-6.9300, 107.6000),
    "Babakan Ciparay": (-6.9400, 107.5800),
    "Bandung Kidul": (-6.9600, 107.6300),
    "Bandung Kulon": (-6.9300, 107.5600),
    "Bandung Wetan": (-6.9000, 107.6200),
    "Batununggal": (-6.9300, 107.6300),
    "Bojongloa Kaler": (-6.9350, 107.5900),
    "Bojongloa Kidul": (-6.9500, 107.5950),
    "Buah Batu": (-6.9500, 107.6400),
    "Cibeunying Kaler": (-6.8850, 107.6300),
    "Cibeunying Kidul": (-6.9000, 107.6400),
    "Cibiru": (-6.9300, 107.7200),
    "Cicendo": (-6.9000, 107.5900),
    "Cidadap": (-6.8600, 107.6100),
    "Cinambo": (-6.9300, 107.7050),
    "Coblong": (-6.8850, 107.6100),
    "Gedebage": (-6.9500, 107.6900),
    "Kiaracondong": (-6.9200, 107.6450),
    "Lengkong": (-6.9300, 107.6200),
    "Mandalajati": (-6.8950, 107.6800),
    "Panyileukan": (-6.9450, 107.7050),
    "Rancasari": (-6.9500, 107.6700),
    "Regol": (-6.9400, 107.6100),
    "Sukajadi": (-6.8850, 107.5850),
    "Sukasari": (-6.8700, 107.5900),
    "Sumur Bandung": (-6.9150, 107.6100),
    "Ujung Berung": (-6.9100, 107.7000),
}


def load_centroids():
    """Opsional: ambil centroid dari CSV OSM Anda bila ada kolom lat/lon."""
    path = os.path.join(os.path.dirname(__file__), "..", "urban_osm_crawler", "output", "urban_osm_features_final.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        cols = {c.lower(): c for c in df.columns}
        name = next((cols[k] for k in ("district", "kecamatan", "name") if k in cols), None)
        lat = next((cols[k] for k in ("lat", "latitude", "centroid_lat") if k in cols), None)
        lon = next((cols[k] for k in ("lon", "lng", "longitude", "centroid_lon") if k in cols), None)
        if name and lat and lon:
            print("Memakai centroid dari", path)
            return {r[name]: (r[lat], r[lon]) for _, r in df.iterrows()}
    print("Memakai koordinat perkiraan bawaan skrip.")
    return DISTRICTS


def get_json(url, params, tries=5):
    for i in range(tries):
        r = requests.get(url, params=params, timeout=60)
        if r.status_code == 200:
            return r.json()
        wait = 5 * (i + 1)
        print(f"  HTTP {r.status_code}, ulangi dalam {wait}s ...")
        time.sleep(wait)
    r.raise_for_status()


def fetch_rainfall(cent):
    rows = []
    for name, (lat, lon) in cent.items():
        print(f"  Fetching hujan: {name} ({lat:.4f}, {lon:.4f})")
        js = get_json(
            "https://archive-api.open-meteo.com/v1/archive",
            {
                "latitude": lat, "longitude": lon,
                "start_date": START, "end_date": END,
                "daily": "precipitation_sum", "timezone": "Asia/Jakarta",
            },
        )
        d = js["daily"]
        for t, p in zip(d["time"], d["precipitation_sum"]):
            rows.append({"district": name, "date": t, "precip_mm": p if p is not None else 0.0})
        time.sleep(1.5)

    daily = pd.DataFrame(rows)
    daily_path = os.path.join(OUT, "rainfall_daily_2021_2023.csv")
    daily.to_csv(daily_path, index=False)
    print(f"  Tersimpan: {daily_path}")

    daily["date"] = pd.to_datetime(daily["date"])
    daily["year"] = daily["date"].dt.year
    daily["precip_mm"] = pd.to_numeric(daily["precip_mm"], errors="coerce").fillna(0)
    daily = daily.sort_values(["district", "date"])
    daily["p3"] = daily.groupby("district")["precip_mm"].transform(lambda s: s.rolling(3).sum())
    feat = daily.groupby(["district", "year"]).agg(
        rainfall_total_mm=("precip_mm", "sum"),
        rainfall_max_1d_mm=("precip_mm", "max"),
        rainfall_max_3d_mm=("p3", "max"),
        days_over_50mm=("precip_mm", lambda s: int((s > 50).sum())),
    ).reset_index()

    feat_path = os.path.join(OUT, "rainfall_features.csv")
    feat.to_csv(feat_path, index=False)
    print(f"  Tersimpan: {feat_path}")
    return daily, feat


def fetch_terrain(cent, d=0.005):
    """Elevasi (Copernicus DEM 90 m via Open-Meteo) di titik tengah + 4 tetangga (~550 m)."""
    pts = []
    for name, (lat, lon) in cent.items():
        for tag, (dy, dx) in {"c": (0, 0), "n": (d, 0), "s": (-d, 0), "e": (0, d), "w": (0, -d)}.items():
            pts.append((name, tag, lat + dy, lon + dx))

    elev = {}
    print(f"  Fetching elevasi untuk {len(pts)} titik...")
    for i in range(0, len(pts), 100):
        chunk = pts[i:i + 100]
        js = get_json(
            "https://api.open-meteo.com/v1/elevation",
            {"latitude": ",".join(f"{p[2]:.5f}" for p in chunk),
             "longitude": ",".join(f"{p[3]:.5f}" for p in chunk)},
        )
        for p, e in zip(chunk, js["elevation"]):
            elev[(p[0], p[1])] = e if e is not None else 700.0
        time.sleep(1.5)

    import math
    rows = []
    for name, (lat, lon) in cent.items():
        step_m = d * 111_000
        elev_c = elev.get((name, "c"), 700.0)
        elev_n = elev.get((name, "n"), elev_c)
        elev_s = elev.get((name, "s"), elev_c)
        elev_e = elev.get((name, "e"), elev_c)
        elev_w = elev.get((name, "w"), elev_c)

        dz_dy = (elev_n - elev_s) / (2 * step_m) if step_m > 0 else 0
        dz_dx = (elev_e - elev_w) / (2 * step_m * math.cos(math.radians(lat))) if step_m > 0 else 0
        slope = math.degrees(math.atan(math.hypot(dz_dx, dz_dy)))
        mean_e = sum([elev_c, elev_n, elev_s, elev_e, elev_w]) / 5

        rows.append({
            "district": name,
            "lat": lat,
            "lon": lon,
            "elevation_mean_m": round(mean_e, 1),
            "slope_mean_deg": round(slope, 2),
        })

    terrain_df = pd.DataFrame(rows)
    terrain_path = os.path.join(OUT, "terrain_features.csv")
    terrain_df.to_csv(terrain_path, index=False)
    print(f"  Tersimpan: {terrain_path}")
    return terrain_df


if __name__ == "__main__":
    print("=" * 65)
    print("UrbanShield AI — Fetch Data Riil (ERA5 + Copernicus DEM)")
    print("=" * 65)

    c = load_centroids()

    print("\n[1/2] Mengambil data terrain (elevasi & slope)...")
    terrain_df = fetch_terrain(c)
    print(terrain_df[["district", "elevation_mean_m", "slope_mean_deg"]].to_string(index=False))

    print("\n[2/2] Mengambil data curah hujan ERA5 (2021-2023)...")
    daily_df, feat_df = fetch_rainfall(c)
    print(feat_df.groupby("district")["rainfall_max_1d_mm"].max().sort_values(ascending=False).head(10))

    print(f"\nSelesai. Cek folder: {OUT}")
    print("Selanjutnya jalankan: python 01b_integrate_real_data.py")
