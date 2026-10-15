# Process GeoJSON downloaded from Overpass Turbo (https://overpass-turbo.eu/)
# Usage: python process_turbo_geojson.py <path_to_geojson>

import sys
import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon

METRIC_CRS = "EPSG:32748"  # UTM 48S for Bandung
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BANDUNG_KECAMATAN = [
    "Andir","Antapani","Arcamanik","Astana Anyar","Babakan Ciparay","Bandung Kidul",
    "Bandung Kulon","Bandung Wetan","Batununggal","Bojongloa Kaler","Bojongloa Kidul",
    "Buah Batu","Cibeunying Kaler","Cibeunying Kidul","Cibiru","Cicendo","Cidadap",
    "Cinambo","Coblong","Gedebage","Kiaracondong","Lengkong","Mandalajati","Panyileukan",
    "Rancasari","Regol","Sukajadi","Sukasari","Sumur Bandung","Ujung Berung",
]

def make_kecamatan_grid():
    from shapely.geometry import box
    # Bandung city bounding box approx
    minx, miny, maxx, maxy = 107.545, -6.970, 107.740, -6.837
    cols, rows = 6, 5
    dx = (maxx - minx) / cols
    dy = (maxy - miny) / rows
    feats = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= len(BANDUNG_KECAMATAN): break
            geom = box(minx + c*dx, miny + r*dy, minx + (c+1)*dx, miny + (r+1)*dy)
            feats.append({"name": BANDUNG_KECAMATAN[idx], "geometry": geom})
            idx += 1
    gdf = gpd.GeoDataFrame(feats, crs="EPSG:4326").to_crs(METRIC_CRS)
    gdf["area_m2"] = gdf.geometry.area
    return gdf

def process(geojson_file):
    print(f"Loading {geojson_file} ...")
    gdf = gpd.read_file(geojson_file)
    print(f"Loaded {len(gdf)} features from GeoJSON")

    kec_gdf = make_kecamatan_grid()
    gdf_metric = gdf.to_crs(METRIC_CRS)

    # Spatial Join with kecamatan
    joined = gpd.sjoin(gdf_metric, kec_gdf, how="inner", predicate="intersects")
    joined = joined.rename(columns={"name_right": "district"})

    districts = kec_gdf["name"].unique()

    # 1. Hydrology (waterways)
    water = joined[joined["waterway"].notna()].copy() if "waterway" in joined.columns else gpd.GeoDataFrame()
    if not water.empty:
        water["length_m"] = water.geometry.length
        river = water[water["waterway"].isin(["river", "stream", "canal"])]
        drain = water[water["waterway"].isin(["drain", "ditch", "culvert"])]
        w_df = pd.DataFrame({"district": districts})
        w_df = w_df.merge(river.groupby("district").size().reset_index(name="river_count"), on="district", how="left")
        w_df = w_df.merge(drain.groupby("district").size().reset_index(name="drainage_count"), on="district", how="left")
        w_df = w_df.merge(river.groupby("district")["length_m"].sum().reset_index(name="river_length_meter"), on="district", how="left")
        w_df = w_df.merge(drain.groupby("district")["length_m"].sum().reset_index(name="drainage_length_meter"), on="district", how="left")
        w_df = w_df.fillna(0)
        area_m2 = kec_gdf.set_index("name")["area_m2"]
        tot_len = w_df["river_length_meter"] + w_df["drainage_length_meter"]
        w_df["water_density"] = (tot_len / area_m2.reindex(w_df["district"]).values).round(6)
    else:
        w_df = pd.DataFrame({"district": districts, "river_count": 0, "river_length_meter": 0.0, "drainage_count": 0, "drainage_length_meter": 0.0, "water_density": 0.0})
    w_df.to_csv(OUTPUT_DIR / "osm_water_features.csv", index=False)

    # 2. Roads
    roads = joined[joined["highway"].notna()].copy() if "highway" in joined.columns else gpd.GeoDataFrame()
    if not roads.empty:
        roads["length_m"] = roads.geometry.length
        r_df = pd.DataFrame({"district": districts})
        r_df = r_df.merge(roads.groupby("district").size().reset_index(name="road_count"), on="district", how="left")
        r_df = r_df.merge(roads.groupby("district")["length_m"].sum().reset_index(name="road_length_meter"), on="district", how="left")
        prim = roads[roads["highway"] == "primary"]
        sec = roads[roads["highway"] == "secondary"]
        r_df = r_df.merge(prim.groupby("district")["length_m"].sum().reset_index(name="primary_road_length"), on="district", how="left")
        r_df = r_df.merge(sec.groupby("district")["length_m"].sum().reset_index(name="secondary_road_length"), on="district", how="left")
        r_df = r_df.fillna(0)
        area_km2 = kec_gdf.set_index("name")["area_m2"] / 1e6
        r_df["road_density"] = (r_df["road_length_meter"] / 1000 / area_km2.reindex(r_df["district"]).values).round(3)
    else:
        r_df = pd.DataFrame({"district": districts, "road_count": 0, "road_length_meter": 0.0, "road_density": 0.0, "primary_road_length": 0.0, "secondary_road_length": 0.0})
    r_df.to_csv(OUTPUT_DIR / "osm_transport_features.csv", index=False)

    # 3. Facilities
    fac = joined[joined["amenity"].notna()].copy() if "amenity" in joined.columns else gpd.GeoDataFrame()
    if not fac.empty:
        f_df = pd.DataFrame({"district": districts})
        for typ in ["hospital", "clinic", "school", "university", "government"]:
            cnt = fac[fac["amenity"] == typ].groupby("district").size().reset_index(name=f"{typ}_count")
            f_df = f_df.merge(cnt, on="district", how="left")
        tot = fac.groupby("district").size().reset_index(name="public_facility_count")
        f_df = f_df.merge(tot, on="district", how="left").fillna(0)
        area_km2 = kec_gdf.set_index("name")["area_m2"] / 1e6
        f_df["facility_density"] = (f_df["public_facility_count"] / area_km2.reindex(f_df["district"]).values).round(3)
    else:
        f_df = pd.DataFrame({"district": districts, "hospital_count": 0, "clinic_count": 0, "school_count": 0, "university_count": 0, "government_count": 0, "public_facility_count": 0, "facility_density": 0.0})
    f_df.to_csv(OUTPUT_DIR / "osm_facility_features.csv", index=False)

    # 4. Buildings
    bld = joined[joined["building"].notna()].copy() if "building" in joined.columns else gpd.GeoDataFrame()
    if not bld.empty:
        b_df = pd.DataFrame({"district": districts})
        b_df = b_df.merge(bld.groupby("district").size().reset_index(name="building_count"), on="district", how="left")
        for typ in ["residential", "commercial"]:
            cnt = bld[bld["building"] == typ].groupby("district").size().reset_index(name=f"{typ}_count")
            b_df = b_df.merge(cnt, on="district", how="left")
        b_df = b_df.fillna(0)
        area_km2 = kec_gdf.set_index("name")["area_m2"] / 1e6
        b_df["building_density"] = (b_df["building_count"] / area_km2.reindex(b_df["district"]).values).round(2)
    else:
        b_df = pd.DataFrame({"district": districts, "building_count": 0, "residential_count": 0, "commercial_count": 0, "building_density": 0.0})
    b_df.to_csv(OUTPUT_DIR / "osm_building_features.csv", index=False)

    # 5. Environment
    has_nat = "natural" in joined.columns
    has_land = "landuse" in joined.columns
    env = joined[(joined["natural"].notna() if has_nat else False) | (joined["landuse"].notna() if has_land else False)].copy()
    if not env.empty:
        env["area_m2"] = env.geometry.area
        green = env[(env["natural"].isin(["wood", "wetland"]) if has_nat else False) | (env["landuse"].isin(["forest", "grass", "farmland"]) if has_land else False)].groupby("district")["area_m2"].sum().reset_index(name="green_area_m2")
        water_a = env[env["natural"] == "water"].groupby("district")["area_m2"].sum().reset_index(name="water_area_m2") if has_nat else pd.DataFrame()
        e_df = pd.DataFrame({"district": districts})
        e_df = e_df.merge(green, on="district", how="left").merge(water_a, on="district", how="left").fillna(0)
        area_m2 = kec_gdf.set_index("name")["area_m2"]
        e_df["green_ratio"] = (e_df["green_area_m2"] / area_m2.reindex(e_df["district"]).values).round(6)
        e_df["water_ratio"] = (e_df["water_area_m2"] / area_m2.reindex(e_df["district"]).values).round(6)
    else:
        e_df = pd.DataFrame({"district": districts, "green_area_m2": 0.0, "green_ratio": 0.0, "water_area_m2": 0.0, "water_ratio": 0.0})
    e_df.to_csv(OUTPUT_DIR / "osm_environment_features.csv", index=False)

    # 6. Final Combined CSV
    final = pd.DataFrame({"district": districts})
    for df in [w_df, r_df, f_df, b_df, e_df]:
        final = final.merge(df, on="district", how="left")
    final = final.fillna(0)
    final_path = OUTPUT_DIR / "urban_osm_features_final.csv"
    final.to_csv(final_path, index=False)

    print(f"\nSUCCESS! 6 CSV files generated in: {OUTPUT_DIR}")
    print(f"urban_osm_features_final.csv shape: {final.shape}")
    print(final.head())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_turbo_geojson.py <path_to_export.geojson>")
        sys.exit(1)
    process(sys.argv[1])
