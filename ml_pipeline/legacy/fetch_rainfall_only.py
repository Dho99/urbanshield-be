"""
fetch_rainfall_only.py  — Retry rainfall fetch dengan checkpoint per kecamatan.
Jalankan beberapa kali jika koneksi terputus; script akan melanjutkan dari yang belum.

    python fetch_rainfall_only.py
"""
import os, time, json, requests, pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUT = BASE_DIR / "data_raw"
OUT.mkdir(exist_ok=True)

CHECKPOINT_DIR = OUT / "_checkpoints"
CHECKPOINT_DIR.mkdir(exist_ok=True)

START, END = "2021-01-01", "2023-12-31"

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


def get_json(url, params, tries=8):
    """Fetch JSON dengan retry eksponensial."""
    import ssl
    session = requests.Session()
    session.verify = True
    for i in range(tries):
        try:
            r = session.get(url, params=params, timeout=90)
            if r.status_code == 200:
                return r.json()
            print(f"  HTTP {r.status_code}, coba lagi {i+1}/{tries}...")
        except Exception as e:
            print(f"  Error: {e.__class__.__name__}: {str(e)[:80]}")
        wait = min(30, 5 * (i + 1))
        print(f"  Tunggu {wait}s...")
        time.sleep(wait)
    raise RuntimeError(f"Gagal setelah {tries} percobaan: {url}")


def fetch_one_district(name, lat, lon):
    """Fetch rainfall untuk satu kecamatan. Return list of row dicts."""
    js = get_json(
        "https://archive-api.open-meteo.com/v1/archive",
        {
            "latitude": lat, "longitude": lon,
            "start_date": START, "end_date": END,
            "daily": "precipitation_sum",
            "timezone": "Asia/Jakarta",
        },
    )
    d = js["daily"]
    rows = []
    for t, p in zip(d["time"], d["precipitation_sum"]):
        rows.append({"district": name, "date": t, "precip_mm": p if p is not None else 0.0})
    return rows


def run():
    total = len(DISTRICTS)
    all_rows = []

    # Load checkpoints yang sudah selesai
    done = set()
    for f in CHECKPOINT_DIR.glob("*.json"):
        done.add(f.stem)
        rows = json.loads(f.read_text())
        all_rows.extend(rows)

    remaining = [(n, c) for n, c in DISTRICTS.items() if n not in done]
    print(f"{'='*60}")
    print(f"Rainfall Fetch — {len(done)}/{total} sudah selesai, {len(remaining)} tersisa")
    print(f"{'='*60}")

    for i, (name, (lat, lon)) in enumerate(remaining, 1):
        print(f"\n[{i}/{len(remaining)}] {name} ({lat:.4f}, {lon:.4f})...")
        try:
            rows = fetch_one_district(name, lat, lon)
            all_rows.extend(rows)
            # Simpan checkpoint
            cp_path = CHECKPOINT_DIR / f"{name}.json"
            cp_path.write_text(json.dumps(rows))
            print(f"  OK — {len(rows)} hari data. Checkpoint disimpan.")
            time.sleep(2.0)  # Jeda agar tidak rate-limited
        except Exception as e:
            print(f"  GAGAL: {e}")
            print(f"  Jalankan ulang script untuk melanjutkan dari sini.")
            break
    else:
        print("\nSemua kecamatan berhasil diambil!")

    if not all_rows:
        print("Tidak ada data yang berhasil diambil.")
        return

    # Simpan CSV gabungan
    daily = pd.DataFrame(all_rows)
    daily["precip_mm"] = pd.to_numeric(daily["precip_mm"], errors="coerce").fillna(0)
    daily_path = OUT / "rainfall_daily_2021_2023.csv"
    daily.to_csv(daily_path, index=False)
    print(f"\nDisimpan: {daily_path} ({len(daily)} baris, {daily['district'].nunique()} kecamatan)")

    # Buat ringkasan fitur
    daily["date"] = pd.to_datetime(daily["date"])
    daily["year"] = daily["date"].dt.year
    daily = daily.sort_values(["district", "date"])
    daily["p3"] = daily.groupby("district")["precip_mm"].transform(lambda s: s.rolling(3).sum())
    feat = daily.groupby(["district", "year"]).agg(
        rainfall_total_mm=("precip_mm", "sum"),
        rainfall_max_1d_mm=("precip_mm", "max"),
        rainfall_max_3d_mm=("p3", "max"),
        days_over_50mm=("precip_mm", lambda s: int((s > 50).sum())),
    ).reset_index()
    feat_path = OUT / "rainfall_features.csv"
    feat.to_csv(feat_path, index=False)
    print(f"Disimpan: {feat_path}")

    # Summary
    print("\n--- Top 10 Kecamatan: Max Hujan 1 Hari (rata-rata 2021-2023) ---")
    summary = feat.groupby("district")["rainfall_max_1d_mm"].mean().sort_values(ascending=False)
    print(summary.head(10).to_string())

    done_count = daily["district"].nunique()
    if done_count == total:
        print(f"\n✅ SELESAI! {done_count}/{total} kecamatan lengkap.")
        print("Selanjutnya: python 01b_integrate_real_data.py")
    else:
        print(f"\n⚠ {done_count}/{total} kecamatan selesai. Jalankan ulang script untuk melanjutkan.")


if __name__ == "__main__":
    run()
