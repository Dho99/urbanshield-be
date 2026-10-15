"""
01_extract_disaster_ground_truth.py
UrbanShield AI — Ekstraksi & Agregasi Data Historis Bencana Resmi Kota Bandung
Sumber Data: Open Data Kota Bandung / Diskar PB / BPBD Kota Bandung 2025
File mentah: backend/urban_osm_crawler/data/lokasi_kejadian_bencana_di_kota_bandung_1.csv
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
CRAWLER_DATA = BASE_DIR.parent / "urban_osm_crawler" / "data" / "lokasi_kejadian_bencana_di_kota_bandung_1.csv"
OSM_FEATURES = BASE_DIR.parent / "urban_osm_crawler" / "output" / "urban_osm_features_final.csv"
OUTPUT_CSV = BASE_DIR / "data" / "bandung_flood_ground_truth.csv"
OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

# Mapping nama kecamatan Kemendagri / BPS ke slug resmi sistem UrbanShield
SLUG_MAP = {
    "ANDIR": "andir",
    "ANTAPANI": "antapani",
    "ARCAMANIK": "arcamanik",
    "ASTANA ANYAR": "astana-anyar",
    "BABAKAN CIPARAY": "babakan-ciparay",
    "BANDUNG KIDUL": "bandung-kidul",
    "BANDUNG KULON": "bandung-kulon",
    "BANDUNG WETAN": "bandung-wetan",
    "BATUNUNGGAL": "batununggal",
    "BOJONGLOA KALER": "bojongloa-kaler",
    "BOJONGLOA KIDUL": "bojongloa-kidul",
    "BUAHBATU": "buah-batu",
    "CIBEUNYING KALER": "cibeunying-kaler",
    "CIBEUNYING KIDUL": "cibeunying-kidul",
    "CIBIRU": "cibiru",
    "CICENDO": "cicendo",
    "CIDADAP": "cidadap",
    "CINAMBO": "cinambo",
    "COBLONG": "coblong",
    "GEDEBAGE": "gedebage",
    "KIARACONDONG": "kiaracondong",
    "LENGKONG": "lengkong",
    "MANDALAJATI": "mandalajati",
    "PANYILEUKAN": "panyileukan",
    "RANCASARI": "rancasari",
    "REGOL": "regol",
    "SUKAJADI": "sukajadi",
    "SUKASARI": "sukasari",
    "SUMUR BANDUNG": "sumur-bandung",
    "UJUNGBERUNG": "ujung-berung",
}

# Standar kapitalisasi tampilan nama kecamatan
DISPLAY_NAMES = {
    "andir": "Andir",
    "antapani": "Antapani",
    "arcamanik": "Arcamanik",
    "astana-anyar": "Astana Anyar",
    "babakan-ciparay": "Babakan Ciparay",
    "bandung-kidul": "Bandung Kidul",
    "bandung-kulon": "Bandung Kulon",
    "bandung-wetan": "Bandung Wetan",
    "batununggal": "Batununggal",
    "bojongloa-kaler": "Bojongloa Kaler",
    "bojongloa-kidul": "Bojongloa Kidul",
    "buah-batu": "Buah Batu",
    "cibeunying-kaler": "Cibeunying Kaler",
    "cibeunying-kidul": "Cibeunying Kidul",
    "cibiru": "Cibiru",
    "cicendo": "Cicendo",
    "cidadap": "Cidadap",
    "cinambo": "Cinambo",
    "coblong": "Coblong",
    "gedebage": "Gedebage",
    "kiaracondong": "Kiaracondong",
    "lengkong": "Lengkong",
    "mandalajati": "Mandalajati",
    "panyileukan": "Panyileukan",
    "rancasari": "Rancasari",
    "regol": "Regol",
    "sukajadi": "Sukajadi",
    "sukasari": "Sukasari",
    "sumur-bandung": "Sumur Bandung",
    "ujung-berung": "Ujung Berung",
}

def main():
    print("=" * 65)
    print("UrbanShield AI — Ekstraksi Data Bencana Resmi Kota Bandung 2025")
    print("=" * 65)

    if not CRAWLER_DATA.exists():
        raise FileNotFoundError(f"File data bencana tidak ditemukan: {CRAWLER_DATA}")

    df_raw = pd.read_csv(CRAWLER_DATA)
    print(f"Memuat {len(df_raw)} catatan kejadian bencana lapangan.")

    df_raw["kec_clean"] = df_raw["kemendagri_nama_kecamatan"].astype(str).str.strip().str.upper()
    df_raw["slug"] = df_raw["kec_clean"].map(SLUG_MAP)

    if df_raw["slug"].isna().any():
        unmapped = df_raw[df_raw["slug"].isna()]["kemendagri_nama_kecamatan"].unique()
        raise ValueError(f"Terdapat kecamatan yang tidak terpetakan: {unmapped}")

    # Definisi kategori bencana
    flood_mask = df_raw["jenis_kejadian"].str.contains("BANJIR", case=False, na=False)
    drainage_mask = df_raw["jenis_kejadian"].str.contains("KIRMIR|TANGGUL", case=False, na=False)
    landslide_mask = df_raw["jenis_kejadian"].str.contains("LONGSOR|AMBLAS", case=False, na=False)
    building_collapse_mask = df_raw["jenis_kejadian"].str.contains("AMBRUK|ROBOH|JEBOL", case=False, na=False) & ~drainage_mask & ~landslide_mask
    wind_fire_mask = df_raw["jenis_kejadian"].str.contains("ANGIN|PUTING|KEBAKARAN|GAS", case=False, na=False)

    records = []
    for raw_name, slug in sorted(SLUG_MAP.items(), key=lambda x: x[1]):
        sub = df_raw[df_raw["slug"] == slug]
        f_count = int(sub["jenis_kejadian"].str.contains("BANJIR", case=False, na=False).sum())
        d_count = int(sub["jenis_kejadian"].str.contains("KIRMIR|TANGGUL", case=False, na=False).sum())
        l_count = int(sub["jenis_kejadian"].str.contains("LONGSOR|AMBLAS", case=False, na=False).sum())
        b_count = int((sub["jenis_kejadian"].str.contains("AMBRUK|ROBOH|JEBOL", case=False, na=False) &
                       ~sub["jenis_kejadian"].str.contains("KIRMIR|TANGGUL|LONGSOR|AMBLAS", case=False, na=False)).sum())
        w_count = int(sub["jenis_kejadian"].str.contains("ANGIN|PUTING|KEBAKARAN|GAS", case=False, na=False).sum())
        total_count = int(len(sub))
        hydromet_count = f_count + d_count

        records.append({
            "districtId": slug,
            "district": DISPLAY_NAMES[slug],
            "flood_events": f_count,
            "drainage_failure_events": d_count,
            "hydromet_events": hydromet_count,
            "landslide_events": l_count,
            "building_collapse_events": b_count,
            "wind_fire_events": w_count,
            "total_disaster_events": total_count,
        })

    df_out = pd.DataFrame(records)
    df_out.to_csv(OUTPUT_CSV, index=False)
    print(f"\n[OK] Ground truth bencana berhasil disimpan ke: {OUTPUT_CSV}")
    print(f"Total Kecamatan: {len(df_out)}")
    print(f"Total Kejadian Banjir: {df_out['flood_events'].sum()} titik")
    print(f"Total Kirmir/Tanggul Ambruk: {df_out['drainage_failure_events'].sum()} titik")
    print(f"Total Bencana Hidrometeorologi: {df_out['hydromet_events'].sum()} titik")
    print(f"Total Seluruh Kejadian Bencana: {df_out['total_disaster_events'].sum()} titik")

    print("\n--- 10 Wilayah Teratas Kejadian Banjir Genangan (Diskar PB 2025) ---")
    top_floods = df_out.sort_values(by="flood_events", ascending=False).head(10)
    print(top_floods[["districtId", "district", "flood_events", "drainage_failure_events", "hydromet_events"]].to_string(index=False))

if __name__ == "__main__":
    main()
