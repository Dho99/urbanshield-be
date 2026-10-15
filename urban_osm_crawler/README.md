# UrbanShield OSM Crawler

> **Geospatial Feature Extraction Pipeline for UrbanShield AI**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![OSM](https://img.shields.io/badge/data-OpenStreetMap-green)](https://www.openstreetmap.org)
[![Overpass API](https://img.shields.io/badge/API-Overpass-orange)](https://wiki.openstreetmap.org/wiki/Overpass_API)

---

## 1. Overview

**UrbanShield OSM Crawler is a geospatial data extraction pipeline that collects urban infrastructure and environmental features from OpenStreetMap using Overpass API. The extracted data is spatially aggregated at district level and prepared as machine learning features for urban flood risk intelligence modeling.**

This repository is **not** a flood prediction model. It is the **Data Acquisition** module of [UrbanShield AI](https://github.com/urbanshield-ai) — *"Explainable Geospatial Intelligence System for Urban Flood Risk Prediction and Mitigation Prioritization"* — responsible for transforming raw OpenStreetMap data into a structured, district-level feature dataset ready for feature engineering and model training.

**Technologies:** Python, Overpass API, GeoPandas, Shapely, PyProj, Pandas, Folium, tqdm

**Data Collected:**

| Category | OSM Keys | Purpose |
|----------|----------|---------|
| Hydrology & Drainage | `waterway` | River and drainage network characterization |
| Transportation | `highway` | Accessibility and impervious surface proxy |
| Critical Facilities | `amenity` | Population exposure assessment |
| Buildings | `building` | Urban density and morphology |
| Environment | `natural`, `landuse` | Infiltration capacity and resilience |

---

## 2. Role in UrbanShield AI Pipeline

The crawler occupies the first stage of the UrbanShield AI pipeline. It produces the foundational geospatial feature layer that is later fused with external datasets to train an explainable risk model.

```
                    ┌─────────────────────────┐
                    │     OpenStreetMap       │
                    │  (Global OSM Database)  │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │ UrbanShield OSM Crawler │  ◄── YOU ARE HERE
                    │ Feature Extraction      │
                    │ Pipeline                │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  Spatial Feature        │
                    │  Dataset (6 CSVs)       │
                    │  District-level grain   │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │  Feature Engineering    │
                    │  Density, Ratio, Score  │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
           ┌──────┐        ┌──────┐        ┌──────────┐
           │ BNPB │        │ BMKG │        │   BPS    │
           │Flood │        │Climate│       │Population│
           │History│       │ Data │        │  Data    │
           └──┬───┘        └──┬───┘        └────┬─────┘
              │               │                 │
              └───────┬───────┴────────┬────────┘
                      │                │
                      ▼                ▼
              ┌──────────────────────────────┐
              │   NASA DEM / Satellite Data  │
              │   (Elevation, Slope, NDVI)   │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  urban_risk_training_dataset │
              │  .csv                        │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Machine Learning Model      │
              │  XGBoost / LightGBM          │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Explainable AI (SHAP)       │
              │  Feature Importance & Rules  │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Mitigation Recommendation   │
              │  UrbanShield Dashboard       │
              └──────────────────────────────┘
```

> **Key distinction:** This crawler does not predict floods. It answers *"what does the urban fabric look like?"* so that downstream models can answer *"where will it flood and why?"*

---

## 3. System Architecture

### 3.1 Data Source

| Component | Description |
|-----------|-------------|
| **OpenStreetMap** | Crowdsourced global geospatial database. Source of truth for infrastructure geometry and tags. |
| **Overpass API** | Read-optimized query engine for OSM. Supports bbox, polygon, area, and tag filters. Public instances: `overpass.private.coffee`, `overpass-api.de`, `maps.mail.ru`. |

### 3.2 Processing

| Stage | Tool | Description |
|-------|------|-------------|
| **API Extraction** | `requests` + retry/fallback | POST `data={query}` with `User-Agent` + `Referer` headers, 40s timeout, multi-server fallback |
| **GeoPandas Processing** | `geopandas`, `shapely`, `pyproj` | Parse Overpass JSON → GeoDataFrame (Point/LineString/Polygon), validate geometries |
| **CRS Handling** | `EPSG:4326` → `EPSG:32748` | WGS84 for API/bbox, UTM Zone 48S (meters) for length/area calculations |
| **Spatial Join** | `gpd.sjoin(predicate="intersects")` | Assign each OSM feature to its `kecamatan` polygon |
| **District Aggregation** | `pandas.groupby` | Count, sum length/area, compute density/ratio per district |

### 3.3 Output

| Format | Location | Purpose |
|--------|----------|---------|
| **CSV** | `output/*.csv` | ML-ready tabular features (6 files) |
| **GeoJSON** | `output/*.geojson` | GIS visualization (city + kecamatan boundaries) |
| **PostGIS-ready** | Schema-compatible | Direct `COPY` into `administrative_boundary`, `osm_*`, `urban_features` tables |

---

## 4. Directory Structure

```
urban_osm_crawler/
├── config.py                  # Pipeline configuration (target region, Overpass servers, CRS, retry policy)
├── crawler.py                 # Main extraction pipeline — Overpass → GeoDataFrame → aggregation → CSV
├── process_turbo_geojson.py   # Alternative path: convert GeoJSON exported from overpass-turbo.eu → CSVs
├── build_dataset.py           # Offline generator for demo/synthetic 30-district dataset (no API call)
├── visualize_osm.py           # Folium validation map generator
├── fallback.py                # Synthetic grid kecamatan fallback when OSM boundary unavailable
├── download_pbf.py            # Optional: Geofabrik PBF download helper (Osmium/PBF workflow)
├── requirements.txt           # Pinned Python dependencies
├── README.md                  # This documentation
├── data/
│   └── raw/                   # Cached PBF / raw Overpass dumps (gitignored)
├── output/                    # Generated datasets (6 CSVs + GeoJSONs)
│   ├── city.geojson
│   ├── kecamatan.geojson
│   ├── osm_water_features.csv
│   ├── osm_transport_features.csv
│   ├── osm_facility_features.csv
│   ├── osm_building_features.csv
│   ├── osm_environment_features.csv
│   ├── urban_osm_features_final.csv
│   └── data_dictionary.csv
└── visualization/
    └── urban_map.html         # Interactive Folium map (heatmap + facility/water layers)
```

| Path | Function |
|------|----------|
| `config.py` | Single source of truth for `TARGET`, `OVERPASS_SERVERS`, `METRIC_CRS`, `MAX_RETRIES`, `TIMEOUT` |
| `crawler.py` | Orchestrates geocoding → kecamatan load → 5 tag-group fetches → 5 aggregations → final merge |
| `output/` | All pipeline outputs; safe to delete and regenerate |
| `visualization/` | QA artifacts; not used for training, only for human validation |

---

## 5. Data Sources

| Dataset | Source | Key Tags | Purpose |
|---------|--------|----------|---------|
| **Waterway** | OpenStreetMap | `waterway=river/stream/canal/drain/ditch/culvert` | Hydrological network density and drainage capacity |
| **Road Network** | OpenStreetMap | `highway=primary/secondary/tertiary/residential/service` | Accessibility, impervious surface, evacuation potential |
| **Facilities** | OpenStreetMap | `amenity=hospital/clinic/school/university/government` | Critical infrastructure exposure |
| **Buildings** | OpenStreetMap | `building=residential/commercial/industrial/*` | Urban density and built-up intensity |
| **Landuse / Natural** | OpenStreetMap | `natural=wood/wetland/water`, `landuse=forest/grass/farmland` | Environmental resilience, infiltration capacity |

All sources are queried via **Overpass QL** against the `area["name"="Bandung"]["boundary"="administrative"]` or a bbox fallback.

---

## 6. Extracted Data Layers

### Hydrology Layer

**Data:** `waterway=river`, `stream`, `canal`, `drain`, `ditch`, `culvert`

| Output Field | Type | Description |
|--------------|------|-------------|
| `river_count` | int | Number of river/stream/canal segments per district |
| `river_length_meter` | float | Total length of rivers (m) |
| `drainage_count` | int | Number of drain/ditch/culvert segments |
| `drainage_length_meter` | float | Total length of drainage channels (m) |
| `water_density` | float | `(river + drainage length) / district area` — hydrological density |

**Relevance:** Represents hydrological load and natural/man-made drainage capacity. Higher `water_density` may indicate flood corridor proximity.

### Transportation Layer

**Data:** `highway=primary`, `secondary`, `tertiary`, `residential`, `service`

| Output Field | Type | Description |
|--------------|------|-------------|
| `road_count` | int | Total road segments |
| `road_length_meter` | float | Total road length (m) |
| `road_density` | float | `road_length_km / area_km²` |
| `primary_road_length` | float | Length of primary roads (m) |
| `secondary_road_length` | float | Length of secondary roads (m) |

**Relevance:** Proxy for impervious surface, urban connectivity, and evacuation accessibility. Dense road networks correlate with sealed surfaces and runoff.

### Facility Layer

**Data:** `amenity=hospital`, `clinic`, `school`, `university`, `government`

| Output Field | Type | Description |
|--------------|------|-------------|
| `hospital_count` | int | Hospitals |
| `clinic_count` | int | Clinics |
| `school_count` | int | Schools |
| `university_count` | int | Universities |
| `government_count` | int | Government facilities |
| `public_facility_count` | int | Sum of all above |
| `facility_density` | float | `facility_count / area_km²` |

**Relevance:** Measures population exposure — districts with dense critical facilities carry higher human and service-disruption risk.

### Building Layer

**Data:** `building=residential`, `commercial`, `industrial`, `retail`, `apartments`, `house`

| Output Field | Type | Description |
|--------------|------|-------------|
| `building_count` | int | Total buildings |
| `residential_count` | int | Residential buildings |
| `commercial_count` | int | Commercial buildings |
| `building_density` | float | `building_count / area_km²` |
| `building_area_m2` | float | Total building footprint (where polygon available) |

**Relevance:** Direct measure of urbanization intensity and surface sealing.

### Environment Layer

**Data:** `natural=wood/wetland/water`, `landuse=forest/grass/farmland`

| Output Field | Type | Description |
|--------------|------|-------------|
| `green_area_m2` | float | Area of wood/wetland/forest/grass/farmland (m²) |
| `green_ratio` | float | `green_area / district area` |
| `water_area_m2` | float | Area of `natural=water` bodies (m²) |
| `water_ratio` | float | `water_area / district area` |

**Relevance:** Captures infiltration and retention capacity. Higher `green_ratio` indicates greater natural flood mitigation potential.

---

## 7. Spatial Processing

| Step | Detail |
|------|--------|
| **Administrative Boundary** | Kota Bandung polygon via Overpass `relation["name"]["admin_level"="7"]` → fallback Nominatim → fallback bbox `107.545,-6.970,107.740,-6.837`. Kecamatan (admin_level 8) via `rel["boundary"="administrative"]["admin_level"="8"](bbox)` or synthetic 6×5 grid fallback. |
| **CRS Conversion** | Ingest in `EPSG:4326` (WGS84) for Overpass bbox; reproject to `EPSG:32748` (UTM Zone 48S) before any `length`/`area` computation. Guarantees meter-accurate metrics. |
| **Spatial Join** | `geopandas.sjoin(features.to_crs(32748), kecamatan.to_crs(32748), predicate="intersects")` — assigns each OSM feature to its district. |
| **Aggregation Level** | **One row = one `kecamatan` (district).** All counts, lengths, and areas are grouped by `district` name. 30 districts for Kota Bandung. |

> **Grain invariant:** Every output CSV has exactly one row per district. No feature-level rows leak into the aggregated outputs.

---

## 8. Output Dataset Documentation

| File | Description | Primary Usage |
|------|-------------|---------------|
| `osm_water_features.csv` | Hydrology features (river/drainage counts, lengths, density) | Hydrological feature engineering |
| `osm_transport_features.csv` | Transportation features (road counts, lengths, density by class) | Accessibility & impervious surface analysis |
| `osm_facility_features.csv` | Critical facility features (hospital/school/etc. counts, density) | Exposure analysis |
| `osm_building_features.csv` | Urban density features (building counts, density, footprint) | Urbanization analysis |
| `osm_environment_features.csv` | Environmental features (green/water area, ratios) | Resilience & infiltration analysis |
| `urban_osm_features_final.csv` | **Merged OSM feature dataset** (all above joined on `district`) | **ML training input — ready for BNPB/BMKG/BPS/DEM join** |

All files are written to `output/` with UTF-8 encoding and header row. Numeric fields are rounded (length 1 decimal, density 3–6 decimals) for clean downstream consumption.

---

## 9. Dataset Grain and Data Dictionary

**Dataset aggregation:** `One row = one district/kecamatan`

**Example (urban_osm_features_final.csv):**

| district | river_count | river_length_meter | road_density | facility_density | building_density | green_ratio |
|----------|:-----------:|:------------------:|:------------:|:----------------:|:----------------:|:-----------:|
| Coblong | 5 | 4820.3 | 15.4 | 0.82 | 420.5 | 0.124 |
| Andir | 2 | 6690.9 | 2.90 | 3.16 | 198.5 | 0.162 |
| Sukajadi | 4 | 3105.2 | 8.21 | 1.45 | 285.3 | 0.089 |

**Data Dictionary:** Full column-level metadata is provided in [`output/data_dictionary.csv`](output/data_dictionary.csv):

| Column | Description |
|--------|-------------|
| `feature name` | Column name as it appears in CSVs |
| `source` | OSM key (`waterway`, `highway`, `amenity`, `building`, `natural`/`landuse`) or derived |
| `description` | Human-readable definition |
| `unit` | `count`, `meter`, `m²`, `ratio`, `km/km²` |

See the file for the complete 26-feature dictionary covering all layers.

---

## 10. Installation

**Requirements:** Python **3.10+** (tested on 3.10–3.13), `pip` 22+

```bat
:: 1. Clone repository
git clone https://github.com/urbanshield-ai/urban_osm_crawler.git
cd urban_osm_crawler

:: 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          :: Windows
:: source venv/bin/activate    :: macOS / Linux

:: 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Core dependencies:** `requests`, `pandas`, `geopandas`, `shapely`, `pyproj`, `tqdm`, `folium`, `python-dotenv`

Optional (PBF workflow): `osmium`

---

## 11. Usage

### Default — Kota Bandung

```bash
python crawler.py
```

Fetches all 5 tag groups for `TARGET = "Kota Bandung, Jawa Barat, Indonesia"` (configured in `config.py`), aggregates per kecamatan, and writes 6 CSVs to `output/`.

### Custom Region

```bash
python crawler.py --region "Surabaya, Jawa Timur, Indonesia"
python crawler.py --region "Kota Medan, Sumatera Utara, Indonesia"
```

The region string is used for both Overpass `area["name"]` lookup and Nominatim geocoding. For best results, use the official administrative name.

### Alternative: From Overpass Turbo Export

If Overpass API is rate-limited, export GeoJSON manually from [overpass-turbo.eu](https://overpass-turbo.eu) (Wizard → Run → Export → GeoJSON), then:

```bash
python process_turbo_geojson.py data/bandung_osm.geojson
```

### Example Output

```
2026-10-01 21:41:47 INFO --- UrbanShield OSM crawler start ---
2026-10-01 21:41:49 INFO Loaded 30 kecamatan polygons
Fetching OSM groups: 100%|████| 5/5 [00:04<00:00, 1.11it/s]
2026-10-01 21:41:55 INFO DONE! Final dataset written to output/urban_osm_features_final.csv
2026-10-01 21:41:55 INFO Crawl finished in 8.0s
```

```csv
district,river_count,river_length_meter,drainage_count,water_density,road_density,facility_density,building_density,green_ratio
Andir,1,6690.9,12,0.001814,2.896,3.156,198.5,0.162249
Coblong,5,4820.3,8,0.001205,15.4,0.82,420.5,0.124000
```

---

## 12. Visualization

The Folium validation map is a **QA tool**, not a training artifact. It lets the data engineering team visually confirm that spatial distributions match expectations before releasing the dataset.

**What it validates:**

- River/drainage clusters align with known watersheds
- Facility markers correspond to real hospital/school locations
- Building density heatmap highlights urban cores
- No district is empty due to a failed spatial join

**Command:**

```bash
python visualize_osm.py
```

**Output:** `visualization/urban_map.html` — open in any browser. Layers are toggleable (Hydrology, Facilities, Heatmap).

> The map uses `OpenStreetMap` tiles (no API key required) and `folium.plugins.HeatMap` for density rendering.

---

## 13. Feature Engineering Guideline

> **For the Feature Engineering team:** The crawler output is **raw aggregated features**, not the final training dataset. The following transformations are recommended before model training.

| Raw Feature (crawler output) | Transformation | Engineered Feature | Rationale |
|------------------------------|---------------|--------------------|-----------|
| `river_length_meter` | `river_length / district_area` | `river_density` | Normalizes by district size |
| `hospital_count + school_count + clinic_count` | Weighted sum / z-score | `critical_facility_score` | Composite exposure index |
| `green_area_m2` | `green_area / district_area` | `green_ratio` | Already provided; use as resilience feature |
| `road_length_meter` | `road_length_km / area_km²` | `road_density` | Already provided; log-transform if skewed |
| `building_count` | `building_count / area_km²` | `building_density` | Already provided; consider `log1p` |
| `water_density`, `road_density`, `building_density` | Min-max or robust scaling | `*_scaled` | Required for tree SHAP comparability |

**Recommended pipeline:**

```python
# 1. Load crawler output
osm = pd.read_csv("output/urban_osm_features_final.csv")

# 2. Derive composite scores
osm["critical_facility_score"] = osm["hospital_count"]*3 + osm["school_count"]*1 + osm["clinic_count"]*1.5
osm["impervious_proxy"] = osm["road_density"] * 0.4 + osm["building_density"] * 0.6
osm["resilience_index"] = osm["green_ratio"] - osm["water_ratio"]

# 3. Join external datasets on `district`
bnpb = pd.read_csv("bnpb_flood_history.csv")
train = osm.merge(bnpb, on="district", how="left")

# 4. Scale for modeling
from sklearn.preprocessing import RobustScaler
```

**Do not** use raw counts without normalization — district areas in Bandung vary 2.5–8.0 km², so counts are not comparable across districts.

---

## 14. Future Integration

```
Crawler Output (6 CSVs, district grain)
        +
  BNPB Flood Historical Data  (flood frequency, depth, duration per district)
        +
  BMKG Climate Data          (rainfall, temperature, humidity time series)
        +
  BPS Population Data        (population density, growth, vulnerability)
        +
  NASA DEM / Satellite       (elevation, slope, NDVI, land surface temp)
                        │
                        ▼
        urban_risk_training_dataset.csv
          (one row = one district × time window)
                        │
                        ▼
              XGBoost / LightGBM
           (gradient boosting classifier/regressor)
                        │
                        ▼
               SHAP Explanation
           (feature importance, dependence plots)
                        │
                        ▼
            UrbanShield Dashboard
     (risk map + mitigation prioritization)
```

| Integration | Join Key | Expected Contribution |
|-------------|----------|-----------------------|
| **BNPB** | `district` + `year` | Target variable (`flood_count`, `flood_severity`) |
| **BMKG** | `district` + `date` | Dynamic trigger features (antecedent rainfall) |
| **BPS** | `district` | Static vulnerability features |
| **NASA DEM** | `district` (zonal stats) | Topographic controls (elevation, slope, TWI) |

---

## 15. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `406 Not Acceptable` / `429 Too Many Requests` | Overpass API rate limit (FOSSGIS: <10k q/day, <1 GB/day) | Wait 30s (per OSM Wiki policy), retry with fallback server (`overpass.private.coffee` → `overpass-api.de` → `maps.mail.ru`). Reduce query size. |
| `504 Gateway Timeout` | Query too large (e.g., `nwr["building"](large_bbox)` with `out geom`) | Split by tag: query `highway~"primary|secondary"` separately; use `out count` first, then `out geom 200` with limit; tile bbox into smaller chunks. |
| `403 Forbidden` from Nominatim | Missing/invalid `User-Agent` or too many requests | Use `User-Agent: UrbanShieldAI/1.0 (contact@...)` + `Referer`; limit to 1 req/s; fallback to Overpass `relation["name"]["admin_level"]` or hardcoded bbox. |
| `CRS mismatch` / wrong distances | Mixing `EPSG:4326` (degrees) with meter math | Always `.to_crs("EPSG:32748")` before `.length` / `.area`. Never compute in 4326. |
| `Empty query result` (0 elements) | Wrong `area` name or server has regional data only | Verify `area["name"="Bandung"]` exists on that instance; try `area["name"~"Bandung",i]`; check `overpass.osm.ch` only serves Switzerland — avoid for Indonesia. |
| `Missing boundary` (0 kecamatan) | `admin_level=8` relations not found in bbox | Crawler falls back to synthetic 6×5 grid (`fallback.py`). For production, supply `data/boundaries/kecamatan.geojson` manually. |
| `sjoin` returns 0 matches | CRS mismatch or invalid geometries | Ensure both GeoDataFrames are in same CRS; run `geom.buffer(0)` to fix self-intersections. |
| `MemoryError` on large city | Fetching all `building=*` for a metropolis | Process per-kecamatan instead of city-wide; use PBF + `osmium` for country-scale extracts. |

**General guidance:** Check `output/city.geojson` and `output/kecamatan.geojson` first. If boundaries look wrong, all downstream aggregations will be wrong.

---

## 16. Development Notes

### Adding a New OSM Tag Group

1. Add an entry to `tag_groups` in `crawler.py`:

   ```python
   "shops": {
       "filter": 'nwr["shop"]',
       "extra": ["shop", "name"],
       "outfile": OUTPUT_DIR / "osm_shop_features.csv"
   }
   ```

2. Add aggregation logic in `main()` (groupby `district`, count/sum).
3. Merge into `final` DataFrame.
4. Document the new layer in Section 6 and `data_dictionary.csv`.

### Changing Target Region

Edit `config.py`:

```python
TARGET = "Kota Surabaya, Jawa Timur, Indonesia"
METRIC_CRS = "EPSG:32749"  # UTM zone 49S for Surabaya (check EPSG for your city)
```

Or pass at runtime: `python crawler.py --region "Kota Surabaya, Jawa Timur, Indonesia"`

> **CRS note:** Bandung uses `EPSG:32748` (UTM 48S). For other cities, look up the correct UTM zone: `326xx` (north) / `327xx` (south).

### Scheduled Crawling

The crawler is a **one-shot** script designed for scheduler wrapping, not internal cron:

```bash
# Weekly refresh every Sunday 02:00
0 2 * * 0 /path/to/venv/bin/python /path/to/crawler.py --region "Kota Bandung, Jawa Barat, Indonesia"
```

Or with `APScheduler` / FastAPI `BackgroundTasks` (see `src/urbanshield/scheduler.py` in the parent project).

### Code Style

- No modification to `crawler.py` core logic without updating this README and `data_dictionary.csv`.
- Keep `config.py` as the single source of truth — no hardcoded regions/URLs in `crawler.py`.
- All new features must maintain the **one row = one district** grain.

---

## License

MIT — see [LICENSE](../LICENSE) for details.

## Acknowledgments

- [OpenStreetMap](https://www.openstreetmap.org) contributors
- [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) by Roland Olbricht
- [Geofabrik](https://download.geofabrik.de) for PBF extracts
- UrbanShield AI team — Data Engineering & Feature Engineering tracks

---

*This crawler is a component of UrbanShield AI. For the full pipeline (model training, SHAP explanation, dashboard), see the parent repository.*
