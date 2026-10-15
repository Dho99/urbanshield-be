"""
01b_integrate_real_data.py
Mengintegrasikan data riil (terrain + rainfall ERA5) ke dalam training_dataset.csv.

Jalankan SETELAH fetch_bandung_data.py selesai:
    python 01b_integrate_real_data.py

Apa yang dilakukan:
1. Baca data_raw/terrain_features.csv  → elevation_mean_m, slope_mean_deg
2. Baca data_raw/rainfall_features.csv → rainfall_max_1d_mm, rainfall_max_3d_mm, days_over_50mm
3. Hitung rainfall_mm per skenario berdasarkan rata-rata max_1d tiap kecamatan
4. Update training_dataset.csv dengan nilai riil (gantikan nilai proxy)
5. Simpan sebagai training_dataset_v2.csv + retrain model otomatis

CATATAN:
  - Jika rainfall ERA5 terlalu rendah untuk skenario heavy rain, tetap pakai
    multiplier skenario agar variasi antar skenario terjaga.
  - Elevation & slope akan menggantikan KECAMATAN_TOPOGRAPHY_DEM di 01_build_training_data.py
"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = BASE_DIR / "data_raw"
ARTIFACTS_DIR = BASE_DIR.parent / "app" / "ml" / "artifacts"

print("=" * 65)
print("UrbanShield AI — Integrasi Data Riil ke Training Dataset")
print("=" * 65)

# -----------------------------------------------------------------------
# 1. Cek ketersediaan file hasil fetch
# -----------------------------------------------------------------------
terrain_path = RAW_DIR / "terrain_features.csv"
rainfall_path = RAW_DIR / "rainfall_features.csv"
training_path = DATA_DIR / "training_dataset.csv"

missing = []
if not terrain_path.exists():
    missing.append(str(terrain_path))
if not rainfall_path.exists():
    missing.append(str(rainfall_path))
if not training_path.exists():
    missing.append(str(training_path))

if missing:
    print("\n[ERROR] File berikut belum ada:")
    for f in missing:
        print(f"  - {f}")
    print("\nJalankan terlebih dahulu:")
    print("  python fetch_bandung_data.py")
    sys.exit(1)

# -----------------------------------------------------------------------
# 2. Baca data riil
# -----------------------------------------------------------------------
print("\n[1/5] Membaca data terrain & curah hujan riil...")
terrain_df = pd.read_csv(terrain_path)
rainfall_feat = pd.read_csv(rainfall_path)
train_df = pd.read_csv(training_path)

print(f"  Terrain: {len(terrain_df)} kecamatan")
print(f"  Rainfall features: {len(rainfall_feat)} baris (kecamatan × tahun)")
print(f"  Training dataset saat ini: {len(train_df)} baris")

# -----------------------------------------------------------------------
# 3. Buat lookup elevasi & slope riil per kecamatan
# -----------------------------------------------------------------------
print("\n[2/5] Membangun lookup elevasi & slope dari Copernicus DEM...")
terrain_lookup = {}
for _, row in terrain_df.iterrows():
    terrain_lookup[row["district"]] = {
        "elevation_mean": round(row["elevation_mean_m"], 1),
        "slope_mean": round(row["slope_mean_deg"], 2),
    }
    print(f"  {row['district']}: elev={row['elevation_mean_m']:.1f}m, slope={row['slope_mean_deg']:.2f}°")

# -----------------------------------------------------------------------
# 4. Buat lookup curah hujan riil per kecamatan (rata-rata 3 tahun)
# -----------------------------------------------------------------------
print("\n[3/5] Membangun lookup curah hujan ERA5 (rata-rata 2021-2023)...")

# Rata-rata fitur rainfall per kecamatan dari 3 tahun
rain_agg = rainfall_feat.groupby("district").agg(
    avg_max_1d_mm=("rainfall_max_1d_mm", "mean"),
    avg_max_3d_mm=("rainfall_max_3d_mm", "mean"),
    avg_days_over50=("days_over_50mm", "mean"),
    avg_total_mm=("rainfall_total_mm", "mean"),
).reset_index()

rain_lookup = {}
for _, row in rain_agg.iterrows():
    rain_lookup[row["district"]] = {
        "avg_max_1d_mm": round(row["avg_max_1d_mm"], 1),
        "avg_max_3d_mm": round(row["avg_max_3d_mm"], 1),
        "avg_days_over50": round(row["avg_days_over50"], 1),
    }

# Rata-rata kota sebagai fallback
city_avg_1d = rain_agg["avg_max_1d_mm"].mean()
print(f"  Rata-rata max hujan 1 hari Kota Bandung (ERA5): {city_avg_1d:.1f} mm")
print(f"  Range: {rain_agg['avg_max_1d_mm'].min():.1f} – {rain_agg['avg_max_1d_mm'].max():.1f} mm")

# -----------------------------------------------------------------------
# 5. Update training dataset dengan nilai riil
# -----------------------------------------------------------------------
print("\n[4/5] Mengupdate training_dataset.csv dengan nilai riil...")

# Multiplier skenario untuk curah hujan (relative ke baseline current)
SCENARIO_RAIN_MULTIPLIER = {
    "current": 1.0,
    "heavy_rain_24h": 2.2,   # ~145mm / ~65mm
    "heavy_rain_72h": 3.8,   # ~245mm / ~65mm
    "drainage_failure": 1.7, # ~110mm / ~65mm
}

updated_count = 0
missing_terrain = []
missing_rain = []

for idx, row in train_df.iterrows():
    district = row["district"]
    scenario = row["scenario"]

    # Update elevasi & slope
    if district in terrain_lookup:
        train_df.at[idx, "elevation_mean"] = terrain_lookup[district]["elevation_mean"]
        train_df.at[idx, "slope_mean"] = terrain_lookup[district]["slope_mean"]
        updated_count += 1
    else:
        missing_terrain.append(district)

    # Update rainfall_mm berdasarkan data ERA5 + multiplier skenario
    if district in rain_lookup:
        base_rain = rain_lookup[district]["avg_max_1d_mm"]
        # Pakai ERA5 sebagai baseline "current", scale untuk skenario lain
        scenario_rain = base_rain * SCENARIO_RAIN_MULTIPLIER.get(scenario, 1.0)
        # Tambahkan variasi orografis kecil berdasarkan elevasi
        elev = train_df.at[idx, "elevation_mean"]
        orographic = (800.0 - elev) * 0.04
        final_rain = round(max(20.0, scenario_rain + orographic * 0.5), 1)
        train_df.at[idx, "rainfall_mm"] = final_rain
    else:
        missing_rain.append(district)

# Recalculate basin_depression_index dari elevasi riil
# (perlu recalculate karena elevasi berubah)
train_df["basin_depression_index"] = train_df["elevation_mean"].apply(
    lambda e: round(max(0.0, min(1.0, (830.0 - e) / (830.0 - 665.0))), 3)
)

# Update effective_drainage_capacity juga tergantung drainage_efficiency per skenario
SCENARIO_DRAIN_EFF = {
    "current": 1.0,
    "heavy_rain_24h": 0.92,
    "heavy_rain_72h": 0.80,
    "drainage_failure": 0.45,
}
for idx, row in train_df.iterrows():
    eff = SCENARIO_DRAIN_EFF.get(row["scenario"], 1.0)
    train_df.at[idx, "effective_drainage_capacity"] = round(row["drainage_density_km"] * eff, 3)

print(f"  Updated {updated_count} baris dengan data terrain riil")
if missing_terrain:
    print(f"  WARNING: {len(set(missing_terrain))} kecamatan tidak ada di terrain data: {set(missing_terrain)}")
if missing_rain:
    print(f"  WARNING: {len(set(missing_rain))} kecamatan tidak ada di rainfall data: {set(missing_rain)}")

# -----------------------------------------------------------------------
# 6. Simpan dataset v2
# -----------------------------------------------------------------------
print("\n[5/5] Menyimpan training_dataset_v2.csv...")
out_v2 = DATA_DIR / "training_dataset_v2.csv"
train_df.to_csv(out_v2, index=False)
print(f"  Tersimpan: {out_v2}")

# Backup dataset lama
backup_path = DATA_DIR / "training_dataset_proxy_backup.csv"
if not backup_path.exists():
    import shutil
    shutil.copy(DATA_DIR / "training_dataset.csv", backup_path)
    print(f"  Backup dataset proxy: {backup_path}")

# -----------------------------------------------------------------------
# 7. Statistik perbandingan
# -----------------------------------------------------------------------
print("\n--- Perbandingan Nilai Elevation (Proxy vs Riil) ---")
orig_df = pd.read_csv(DATA_DIR / "training_dataset.csv")
compare = train_df[train_df["scenario"] == "current"][["district", "elevation_mean", "slope_mean", "rainfall_mm"]].copy()
compare.columns = ["district", "elev_riil", "slope_riil", "rain_current_riil"]
orig_current = orig_df[orig_df["scenario"] == "current"][["district", "elevation_mean", "slope_mean", "rainfall_mm"]].copy()
orig_current.columns = ["district", "elev_proxy", "slope_proxy", "rain_current_proxy"]
compare_df = compare.merge(orig_current, on="district")
compare_df["elev_diff"] = compare_df["elev_riil"] - compare_df["elev_proxy"]
print(compare_df[["district", "elev_proxy", "elev_riil", "elev_diff"]].to_string(index=False))

print("\n--- Statistik Rainfall ERA5 vs Proxy ---")
print(f"  Proxy current avg: {orig_df[orig_df['scenario']=='current']['rainfall_mm'].mean():.1f} mm")
print(f"  ERA5 current avg:  {train_df[train_df['scenario']=='current']['rainfall_mm'].mean():.1f} mm")

# -----------------------------------------------------------------------
# 8. Auto-retrain model dengan data baru
# -----------------------------------------------------------------------
print("\n" + "=" * 65)
print("Dataset v2 siap. Jalankan retrain model:")
print("  python 02_train_model.py --input data/training_dataset_v2.csv")
print("=" * 65)
print("\nAtau copy manual dan jalankan:")
print("  copy data\\training_dataset_v2.csv data\\training_dataset.csv")
print("  python 02_train_model.py")
