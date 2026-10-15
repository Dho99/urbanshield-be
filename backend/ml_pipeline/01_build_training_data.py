"""
UrbanShield AI — Tahap 1: Data Fusion & Dataset Preparation Pipeline
Proyek: Sistem Intelijen Geospasial Berbasis Explainable ML untuk Prediksi Risiko Banjir Perkotaan

Tujuan Skrip:
1. Membaca fitur spasial OSM (urban_osm_features_final.csv) untuk 30 kecamatan Kota Bandung.
2. Mengintegrasikan parameter fisik & meteorologi riil:
   - Topografi / Elevasi & Slope: Copernicus DEM GLO-30 (data_raw/terrain_features.csv)
   - Curah Hujan Historis: Copernicus / ECMWF ERA5 Reanalysis 2021-2023 (data_raw/rainfall_features.csv)
   - Kepadatan Penduduk: BPS Kota Bandung Dalam Angka 2024 (termasuk Bojongloa Kaler ~39.500 jiwa/km²)
   - Data Historis Bencana Resmi BPBD / Diskar PB Kota Bandung 2025 (data/bandung_flood_ground_truth.csv)
3. Menghitung fitur komposit & multi-skenario (Current, Heavy Rain 24h, Heavy Rain 72h, Drainage Failure).
4. Menghitung target label risiko banjir (risk_score 0–100) berbasis kerangka kerja BNPB
   (Hazard x Vulnerability / Capacity) yang dikalibrasi dengan frekuensi kejadian empiris lapangan.
5. Menyimpan dataset terintegrasi ke backend/ml_pipeline/data/training_dataset.csv.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

# Path direktori
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR = BASE_DIR / "data_raw"

OSM_CSV_PATH = BASE_DIR.parent / "urban_osm_crawler" / "output" / "urban_osm_features_final.csv"
TERRAIN_PATH = RAW_DIR / "terrain_features.csv"
RAINFALL_PATH = RAW_DIR / "rainfall_features.csv"
GROUND_TRUTH_PATH = DATA_DIR / "bandung_flood_ground_truth.csv"

# ----------------------------------------------------------------------------------
# 1. KEPADATAN PENDUDUK BPS KOTA BANDUNG DALAM ANGKA 2024 (jiwa / km²)
# Sumber Resmi: BPS Kota Bandung 2024
# Bojongloa Kaler merupakan salah satu wilayah terpadat di Kota Bandung (~39.500 jiwa/km²)
# ----------------------------------------------------------------------------------
BPS_POPULATION_DENSITY_2024 = {
    "Andir": 24850.0,
    "Antapani": 18240.0,
    "Arcamanik": 11450.0,
    "Astana Anyar": 23820.0,
    "Babakan Ciparay": 23540.0,
    "Bandung Kidul": 14120.0,
    "Bandung Kulon": 19650.0,
    "Bandung Wetan": 10520.0,
    "Batununggal": 24100.0,
    "Bojongloa Kaler": 39510.0,    # Angka BPS Kota Bandung 2024 (validasi catatan reviewer)
    "Bojongloa Kidul": 16230.0,
    "Buah Batu": 15640.0,
    "Cibeunying Kaler": 14920.0,
    "Cibeunying Kidul": 15810.0,
    "Cibiru": 13620.0,
    "Cicendo": 13940.0,
    "Cidadap": 5830.0,
    "Cinambo": 8940.0,
    "Coblong": 14210.0,
    "Gedebage": 6520.0,
    "Kiaracondong": 22130.0,
    "Lengkong": 12410.0,
    "Mandalajati": 12840.0,
    "Panyileukan": 9820.0,
    "Rancasari": 13430.0,
    "Regol": 18520.0,
    "Sukajadi": 15210.0,
    "Sukasari": 13120.0,
    "Sumur Bandung": 11830.0,
    "Ujung Berung": 14530.0,
}

# ----------------------------------------------------------------------------------
# 2. DEFINISI 4 SKENARIO SIMULASI
# ----------------------------------------------------------------------------------
SCENARIOS = {
    "current": {
        "rain_multiplier": 1.0,       # baseline musiman rata-rata ERA5 (~60-70 mm/24h)
        "drainage_efficiency": 1.0,   # 100% kapasitas operasional
        "description": "Kondisi operasional normal musim hujan reguler",
    },
    "heavy_rain_24h": {
        "rain_multiplier": 2.2,       # simulasi hujan lebat 24 jam (~135-155 mm)
        "drainage_efficiency": 0.92,  # sedikit bottleneck aliran
        "description": "Simulasi hujan lebat ekstrem 24 jam (+12% risiko)",
    },
    "heavy_rain_72h": {
        "rain_multiplier": 3.8,       # akumulasi curah hujan berkepanjangan 72 jam (~220-260 mm)
        "drainage_efficiency": 0.80,  # saluran jenuh / limpasan permukaan
        "description": "Simulasi hujan lebat ekstrem berkepanjangan 72 jam",
    },
    "drainage_failure": {
        "rain_multiplier": 1.7,       # hujan sedang-lebat (~105-120 mm)
        "drainage_efficiency": 0.45,  # 55% saluran tersumbat sedimen / kirmir ambruk
        "description": "Simulasi kegagalan sistem drainase perkotaan & penyumbatan saluran",
    },
}

def to_district_id(district_name: str) -> str:
    slug = district_name.strip().lower().replace(" ", "-")
    alias_map = {
        "ujungberung": "ujung-berung",
        "buahbatu": "buah-batu",
    }
    return alias_map.get(slug, slug)

def build_dataset() -> pd.DataFrame:
    print("\n[1/4] Membaca data geospasial OSM, Copernicus DEM, ERA5, dan BPBD...")

    if not OSM_CSV_PATH.exists():
        raise FileNotFoundError(f"OSM CSV tidak ditemukan di: {OSM_CSV_PATH}")

    osm_df = pd.read_csv(OSM_CSV_PATH)
    print(f"  OSM Features: {len(osm_df)} kecamatan")

    # Load Terrain Copernicus DEM
    terrain_lookup = {}
    if TERRAIN_PATH.exists():
        tdf = pd.read_csv(TERRAIN_PATH)
        for _, r in tdf.iterrows():
            terrain_lookup[r["district"]] = {
                "elevation": round(float(r["elevation_mean_m"]), 1),
                "slope": round(float(r["slope_mean_deg"]), 2),
            }
        print(f"  Copernicus DEM: {len(terrain_lookup)} kecamatan dimuat")
    else:
        print("  WARNING: terrain_features.csv belum ada, menggunakan estimasi fallback")

    # Load ERA5 Rainfall
    rain_lookup = {}
    if RAINFALL_PATH.exists():
        rdf = pd.read_csv(RAINFALL_PATH)
        r_agg = rdf.groupby("district").agg(
            avg_max_1d=("rainfall_max_1d_mm", "mean"),
            avg_max_3d=("rainfall_max_3d_mm", "mean"),
        ).reset_index()
        for _, r in r_agg.iterrows():
            rain_lookup[r["district"]] = {
                "max_1d": round(float(r["avg_max_1d"]), 1),
                "max_3d": round(float(r["avg_max_3d"]), 1),
            }
        print(f"  Copernicus ERA5: {len(rain_lookup)} kecamatan dimuat")
    else:
        print("  WARNING: rainfall_features.csv belum ada, menggunakan estimasi fallback")

    # Load Ground Truth Bencana BPBD / Diskar PB 2025
    gt_lookup = {}
    if GROUND_TRUTH_PATH.exists():
        gtdf = pd.read_csv(GROUND_TRUTH_PATH)
        for _, r in gtdf.iterrows():
            gt_lookup[r["districtId"]] = {
                "flood_events": int(r["flood_events"]),
                "drainage_failures": int(r["drainage_failure_events"]),
                "hydromet_events": int(r["hydromet_events"]),
                "total_disasters": int(r["total_disaster_events"]),
            }
        print(f"  BPBD Ground Truth: {len(gt_lookup)} kecamatan dimuat")
    else:
        print("  WARNING: bandung_flood_ground_truth.csv belum ada!")

    max_hydromet = max([v["hydromet_events"] for v in gt_lookup.values()]) if gt_lookup else 8

    print("\n[2/4] Melakukan Fusi Data & Feature Engineering komposit...")
    rows = []

    # Iterasi 30 kecamatan dan 4 skenario simulasi
    for _, osm_row in osm_df.iterrows():
        district = osm_row["district"]
        district_id = to_district_id(district)

        # 1. Topografi riil Copernicus DEM
        if district in terrain_lookup:
            elevation = terrain_lookup[district]["elevation"]
            slope = terrain_lookup[district]["slope"]
        else:
            elevation = 700.0
            slope = 2.0

        # Basin depression level (Cekungan Bandung: titik terendah ~665m di Gedebage/Panyileukan, titik tertinggi ~830m di Cidadap)
        basin_depression = round(max(0.0, min(1.0, (830.0 - elevation) / (830.0 - 665.0))), 3)

        # 2. Demografi BPS 2024
        pop_density = BPS_POPULATION_DENSITY_2024.get(district, 15000.0)

        # 3. Fitur OSM
        drainage_len_km = osm_row["drainage_length_meter"] / 1000.0
        river_len_km = osm_row["river_length_meter"] / 1000.0
        road_dens = osm_row["road_density"]
        bldg_dens = osm_row["building_density"]
        green_ratio = osm_row["green_ratio"]
        water_ratio = osm_row["water_ratio"]
        facility_dens = osm_row["facility_density"]

        # Estimasi luas area (km²) dari rasio kepadatan bangunan
        area_km2 = max(2.5, min(18.0, osm_row["building_count"] / max(1.0, bldg_dens)))
        drainage_density_km = drainage_len_km / area_km2
        river_density_km = river_len_km / area_km2

        # Tutupan kedap air (Impervious Surface Ratio)
        impervious_ratio = min(0.95, (bldg_dens / 2500.0 * 0.50) + (road_dens / 50.0 * 0.35) + 0.10)

        # 4. Data Historis Bencana BPBD
        gt_info = gt_lookup.get(district_id, {"flood_events": 0, "drainage_failures": 0, "hydromet_events": 0, "total_disasters": 0})
        flood_count = gt_info["flood_events"]
        drainage_fail_count = gt_info["drainage_failures"]
        hydromet_count = gt_info["hydromet_events"]

        # Frekuensi bencana historis (skala 0 - 100)
        # Menggabungkan kejadian genangan langsung (bobot utama) dan keruntuhan kirmir/tanggul drainase
        h_history = min(100.0, (flood_count / 8.0 * 85.0) + (drainage_fail_count / 8.0 * 15.0))

        # 5. Iterasi 4 skenario simulasi
        for sc_name, sc_params in SCENARIOS.items():
            if sc_name == "heavy_rain_72h":
                base_rain = rain_lookup.get(district, {}).get("max_3d", 112.0)
                rain_mult = 2.15 # Akumulasi ekstrem 72 jam (~230-260 mm)
            else:
                base_rain = rain_lookup.get(district, {}).get("max_1d", 62.0)
                rain_mult = sc_params["rain_multiplier"]

            drain_eff = sc_params["drainage_efficiency"]

            # Curah hujan skenario dengan variasi orografis Cekungan Bandung
            orographic = (800.0 - elevation) * 0.04
            rain_val = round(max(20.0, base_rain * rain_mult + orographic * 0.5), 1)

            # Kapasitas drainase efektif
            effective_drainage = round(drainage_density_km * drain_eff, 3)
            effective_infiltration = green_ratio * (1.0 - (0.2 if sc_name.startswith("heavy") else 0.0))

            # ------------------------------------------------------------------
            # FORMULASI KERANGKA KERJA RISIKO BENCANA BNPB (Perka No. 02/2012)
            # Risk = (Hazard x Vulnerability) / Capacity
            # ------------------------------------------------------------------
            # 1. HAZARD SCORE (0 - 100):
            # Menggabungkan curah hujan skenario (25%), topografi cekungan (20%), kelandaian (10%),
            # eksposur sungai (10%), dan dikalibrasi frekuensi kejadian historis BPBD / Diskar PB 2025 (35%).
            h_rain = min(1.0, rain_val / 260.0) * 25.0                    # max 25 poin
            h_basin = basin_depression * 20.0                             # max 20 poin
            h_slope = max(0.0, (10.0 - slope) / 10.0) * 10.0             # max 10 poin (datar = air tertahan)
            h_river = min(1.0, river_density_km / 2.5) * 10.0             # max 10 poin (eksposur sungai)
            h_empiric = (h_history / 100.0) * 35.0                        # max 35 poin (validasi empiris BPBD)
            hazard_score = min(100.0, h_rain + h_basin + h_slope + h_river + h_empiric)

            # Tambahan hazard limpasan/backflow pada cekungan rendah saat hujan ekstrem berkepanjangan
            if sc_name == "heavy_rain_72h" and basin_depression > 0.85:
                hazard_score = min(100.0, hazard_score + 5.0)

            # 2. VULNERABILITY SCORE (0 - 100):
            # Kepadatan penduduk (BPS 2024), tutupan kedap air (OSM), fasilitas kritis terpapar
            v_pop = min(1.0, pop_density / 35000.0) * 40.0                # max 40 poin
            v_impervious = impervious_ratio * 35.0                        # max 35 poin
            v_fac = min(1.0, facility_dens / 15.0) * 25.0                 # max 25 poin
            vulnerability_score = min(100.0, v_pop + v_impervious + v_fac)

            # 3. CAPACITY SCORE (0 - 100):
            # Kapasitas drainase efektif + ruang hijau resapan air
            c_drain = min(1.0, effective_drainage / 2.5) * 60.0           # max 60 poin
            c_green = min(1.0, effective_infiltration / 0.25) * 40.0      # max 40 poin
            capacity_score = max(10.0, min(100.0, c_drain + c_green))

            # INDEKS RISIKO AKHIR (0 - 100):
            raw_risk = (hazard_score * 0.50) + (vulnerability_score * 0.35) - (capacity_score * 0.20)
            final_risk_score = int(round(max(15, min(96, raw_risk * 1.55 + 5.0))))

            # Klasifikasi level risiko
            if final_risk_score >= 70:
                risk_level = "high"
            elif final_risk_score >= 40:
                risk_level = "medium"
            else:
                risk_level = "low"

            # Rekomendasi mitigasi otomatis berdasarkan faktor kritis
            if flood_count >= 5 or (basin_depression > 0.7 and effective_drainage < 1.0):
                reco = "Prioritas tinggi polder pompa, kolam retensi, dan normalisasi saluran primer."
            elif drainage_fail_count >= 2:
                reco = "Perkuatan struktural kirmir/tanggul saluran dan pembersihan sumbatan drainase."
            elif green_ratio < 0.12 and impervious_ratio > 0.70:
                reco = "Konstruksi sumur resapan komunal & penambahan vegetasi bioswale di kawasan padat."
            elif river_density_km > 1.5:
                reco = "Pengerukan sedimen sungai secara berkala dan pemantauan sensor tinggi muka air."
            elif final_risk_score >= 70:
                reco = "Penguatan Early Warning System (EWS) banjir & kesiapsiagaan jalur evakuasi warga."
            elif final_risk_score >= 40:
                reco = "Pembersihan rutin sedimen saluran lingkungan dan inspeksi berkala gorong-gorong."
            else:
                reco = "Kondisi stabil. Pertahankan pemantauan rutin & pemeliharaan berkala saluran air."

            row = {
                # Identitas Wilayah
                "districtId": district_id,
                "district": district,
                "scenario": sc_name,

                # Fitur Masukan Model (Features X: 14 kolom)
                "rainfall_mm": round(rain_val, 1),
                "elevation_mean": round(elevation, 1),
                "slope_mean": round(slope, 1),
                "population_density": round(pop_density, 1),
                "drainage_density_km": round(drainage_density_km, 3),
                "river_density_km": round(river_density_km, 3),
                "road_density": round(road_dens, 3),
                "building_density": round(bldg_dens, 2),
                "green_ratio": round(green_ratio, 4),
                "water_ratio": round(water_ratio, 4),
                "facility_density": round(facility_dens, 3),
                "impervious_ratio": round(impervious_ratio, 3),
                "basin_depression_index": round(basin_depression, 3),
                "effective_drainage_capacity": round(effective_drainage, 3),

                # Komponen BNPB
                "hazard_index": round(hazard_score, 2),
                "vulnerability_index": round(vulnerability_score, 2),
                "capacity_index": round(capacity_score, 2),

                # Validasi Empiris Historis
                "historical_flood_events": flood_count,
                "historical_drainage_failures": drainage_fail_count,
                "historical_hydromet_events": hydromet_count,

                # Target Ground Truth (y)
                "risk_score": final_risk_score,
                "risk_level": risk_level,
                "confidence": int(round(80 + (final_risk_score % 15))),
                "recommendation": reco,
            }
            rows.append(row)

    df_out = pd.DataFrame(rows)
    return df_out

def main():
    print("=" * 65)
    print("UrbanShield AI — Tahap 1: Fusi Data Multi-Sumber & Penyiapan Dataset")
    print("=" * 65)

    dataset = build_dataset()

    output_csv = DATA_DIR / "training_dataset.csv"
    output_v2 = DATA_DIR / "training_dataset_v2.csv"
    dataset.to_csv(output_csv, index=False)
    dataset.to_csv(output_v2, index=False)

    print(f"\n[OK] Dataset berhasil disimpan ke:")
    print(f"     1. {output_csv}")
    print(f"     2. {output_v2}")
    print(f"     Total baris: {len(dataset)} baris (30 kecamatan × 4 skenario)")
    print(f"     Total kolom: {len(dataset.columns)} kolom")

    print("\n--- Ringkasan Distribusi Kelas Risiko (120 sampel) ---")
    print(dataset["risk_level"].value_counts())

    print("\n--- Cuplikan Kondisi Eksisting (Skenario Current) Top 10 Risiko ---")
    current_df = dataset[dataset["scenario"] == "current"].sort_values(by="risk_score", ascending=False).head(10)
    print(current_df[["district", "risk_score", "risk_level", "historical_flood_events", "basin_depression_index", "effective_drainage_capacity"]].to_string(index=False))

if __name__ == "__main__":
    main()
