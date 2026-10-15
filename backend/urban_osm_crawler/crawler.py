import argparse
import json
import logging
import time
import re
from pathlib import Path
from typing import Dict, List

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import shape, Polygon, MultiPolygon, Point, LineString
from tqdm import tqdm

from config import (
    TARGET,
    OVERPASS_SERVERS,
    OUTPUT_DIR,
    METRIC_CRS,
    MAX_RETRIES,
    BACKOFF_SECONDS,
    TIMEOUT,
    LOG_LEVEL,
)
from fallback import make_fallback_kecamatan, BANDUNG_KECAMATAN

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()), format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def overpass_fetch(query: str) -> dict:
    headers = {
        "User-Agent": "UrbanShieldAI/1.0 (contact: info@urbanshield.ai)",
        "Accept": "application/json",
    }
    for server in OVERPASS_SERVERS:
        try:
            resp = requests.post(server, data={"data": query}, headers=headers, timeout=40)
            if resp.status_code == 200:
                j = resp.json()
                if "elements" in j:
                    return j
        except Exception as e:
            logger.debug(f"{server} fail: {e}")
        time.sleep(1)
    raise RuntimeError("All Overpass servers failed")

def get_region_polygon(place: str) -> gpd.GeoDataFrame:
    query = f'[out:json][timeout:40];relation["name"="{place.split(",")[0].strip()}"]["boundary"="administrative"]["admin_level"="7"];out geom;'
    try:
        data = overpass_fetch(query)
        for el in data.get("elements", []):
            if el["type"] == "relation":
                polys = []
                for m in el.get("members", []):
                    if m.get("role") in ("outer", "") and m.get("geometry"):
                        c = [(p["lon"], p["lat"]) for p in m["geometry"]]
                        if len(c) >= 4:
                            try: polys.append(Polygon(c))
                            except Exception: pass
                if polys:
                    geom = MultiPolygon(polys) if len(polys) > 1 else polys[0]
                    if not geom.is_valid: geom = geom.buffer(0)
                    return gpd.GeoDataFrame([{"name": el.get("tags", {}).get("name", place), "osm_id": el["id"], "admin_level": 7, "geometry": geom}], crs="EPSG:4326")
    except Exception as e:
        logger.warning(f"Overpass city boundary fail: {e}")

    headers = {"User-Agent": "UrbanShieldAI_Crawler/1.0 (info@urbanshield.ai)"}
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "polygon_geojson": 1, "limit": 1}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if data:
                geom = shape(data[0]["geojson"])
                if geom.geom_type == "Polygon": geom = MultiPolygon([geom])
                return gpd.GeoDataFrame([{"name": data[0]["display_name"], "osm_id": data[0]["osm_id"], "admin_level": 7, "geometry": geom}], crs="EPSG:4326")
    except Exception as e:
        logger.warning(f"Nominatim fail: {e}")

    from shapely.geometry import box
    geom = box(107.545, -6.970, 107.740, -6.837)
    return gpd.GeoDataFrame([{"name": place, "osm_id": 0, "admin_level": 7, "geometry": MultiPolygon([geom])}], crs="EPSG:4326")

def json_to_gdf(data: dict, extra_cols: List[str]) -> gpd.GeoDataFrame:
    rows = []
    for el in data.get("elements", []):
        t = el.get("type")
        tags = el.get("tags", {}) or {}
        osm_id = el.get("id")
        geom = None
        if t == "node" and "lon" in el and "lat" in el:
            geom = Point(el["lon"], el["lat"])
        elif t == "way":
            pts = el.get("geometry", [])
            if not pts: continue
            coords = [(p["lon"], p["lat"]) for p in pts]
            if len(coords) >= 4 and coords[0] == coords[-1]:
                try:
                    geom = Polygon(coords)
                    if not geom.is_valid: geom = geom.buffer(0)
                except Exception:
                    geom = LineString(coords)
            else:
                geom = LineString(coords)
        else: continue
        if geom is None or geom.is_empty: continue
        row = {"osm_id": osm_id, "osm_type": t, "tags": json.dumps(tags, ensure_ascii=False)}
        for col in extra_cols: row[col] = tags.get(col)
        row["geometry"] = geom
        rows.append(row)
    if not rows: return gpd.GeoDataFrame(columns=["osm_id", "geometry"], crs="EPSG:4326")
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")

def load_kecamatan(city_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    bbox = city_gdf.to_crs("EPSG:4326").total_bounds
    min_lon, min_lat, max_lon, max_lat = bbox
    q = f'[out:json][timeout:40];(rel["boundary"="administrative"]["admin_level"="8"]({min_lat},{min_lon},{max_lat},{max_lon}););out geom;'
    try:
        data = overpass_fetch(q)
        feats = []
        for el in data.get("elements", []):
            if el.get("type") != "relation": continue
            tags = el.get("tags", {})
            name = tags.get("name", f"rel-{el['id']}")
            polys = []
            for m in el.get("members", []):
                if m.get("role") in ("outer", "") and m.get("geometry"):
                    c = [(p["lon"], p["lat"]) for p in m["geometry"]]
                    if len(c) >= 4:
                        try: polys.append(Polygon(c))
                        except Exception: pass
            if not polys: continue
            geom = MultiPolygon(polys) if len(polys) > 1 else polys[0]
            if not geom.is_valid: geom = geom.buffer(0)
            feats.append({"name": name, "osm_id": el["id"], "geometry": geom, "admin_level": 8})
        if feats:
            gdf = gpd.GeoDataFrame(feats, crs="EPSG:4326").drop_duplicates("name").sort_values("name").reset_index(drop=True)
            gdf = gdf.to_crs(METRIC_CRS)
            gdf["area_m2"] = gdf.geometry.area
            return gdf
    except Exception as e:
        logger.warning(f"Kecamatan fetch failed: {e}")

    logger.warning("Using synthetic grid kecamatan boundary fallback")
    return make_fallback_kecamatan(city_gdf, METRIC_CRS)

def main(region: str = TARGET):
    start = time.time()
    logger.info("--- UrbanShield OSM crawler start ---")
    city_gdf = get_region_polygon(region)
    city_gdf_metric = city_gdf.to_crs(METRIC_CRS)
    kec_gdf = load_kecamatan(city_gdf)
    logger.info(f"Loaded {len(kec_gdf)} kecamatan polygons")
    
    city_gdf.to_file(OUTPUT_DIR / "city.geojson", driver="GeoJSON")
    kec_gdf.to_file(OUTPUT_DIR / "kecamatan.geojson", driver="GeoJSON")

    bbox = city_gdf.to_crs("EPSG:4326").total_bounds
    min_lon, min_lat, max_lon, max_lat = bbox
    bbox_str = f"{min_lat},{min_lon},{max_lat},{max_lon}"

    tag_groups: Dict[str, Dict] = {
        "water": {"filter": 'nwr["waterway"]', "extra": ["waterway", "name"], "outfile": OUTPUT_DIR / "osm_water_features.csv"},
        "roads": {"filter": 'nwr["highway"]', "extra": ["highway", "surface", "lanes", "name"], "outfile": OUTPUT_DIR / "osm_transport_features.csv"},
        "facilities": {"filter": 'nwr["amenity"~"hospital|clinic|school|university|government"]', "extra": ["amenity", "name"], "outfile": OUTPUT_DIR / "osm_facility_features.csv"},
        "buildings": {"filter": 'nwr["building"]', "extra": ["building", "name"], "outfile": OUTPUT_DIR / "osm_building_features.csv"},
        "environment": {"filter": 'nwr["natural"~"wood|wetland|water"]', "extra": ["natural", "landuse", "name"], "outfile": OUTPUT_DIR / "osm_environment_features.csv"},
    }

    results = {}
    for name, cfg in tqdm(tag_groups.items(), desc="Fetching OSM groups"):
        filt = cfg["filter"]
        q = f'[out:json][timeout:45];({filt}({bbox_str}););out geom;'
        try:
            data = overpass_fetch(q)
            gdf = json_to_gdf(data, cfg["extra"])
            logger.info(f"Fetched {len(gdf)} features for {name}")
        except Exception as e:
            logger.warning(f"Fetch {name} failed: {e}, using empty GeoDataFrame")
            gdf = gpd.GeoDataFrame(columns=["osm_id", "geometry"], crs="EPSG:4326")
        results[name] = gdf

    kec_metric = kec_gdf

    # 1. Water
    w_gdf = results.get("water")
    if w_gdf is not None and not w_gdf.empty:
        w = w_gdf.to_crs(METRIC_CRS)
        w["length_m"] = w.geometry.length
        j = gpd.sjoin(w, kec_metric, how="inner", predicate="intersects").rename(columns={"name_right": "district"})
        river = j[j.get("waterway", pd.Series()).isin(["river", "stream", "canal"])]
        drain = j[j.get("waterway", pd.Series()).isin(["drain", "ditch", "culvert"])]
        agg = pd.DataFrame({"district": kec_metric["name"].unique()})
        agg = agg.merge(river.groupby("district").size().reset_index(name="river_count"), how="left", on="district")
        agg = agg.merge(drain.groupby("district").size().reset_index(name="drainage_count"), how="left", on="district")
        agg = agg.merge(river.groupby("district")["length_m"].sum().reset_index(name="river_length_meter"), how="left", on="district")
        agg = agg.merge(drain.groupby("district")["length_m"].sum().reset_index(name="drainage_length_meter"), how="left", on="district")
        agg = agg.fillna(0)
        agg["river_length_meter"] = agg["river_length_meter"].round(1)
        agg["drainage_length_meter"] = agg["drainage_length_meter"].round(1)
        denom = kec_metric.set_index("name")["area_m2"]
        agg["water_density"] = ((agg["river_length_meter"] + agg["drainage_length_meter"]) / denom.reindex(agg["district"]).values).round(6)
        agg.to_csv(OUTPUT_DIR / "osm_water_features.csv", index=False)
        results["water_agg"] = agg
    else:
        agg = pd.DataFrame({"district": kec_metric["name"].unique(), "river_count": 0, "river_length_meter": 0.0, "drainage_count": 0, "drainage_length_meter": 0.0, "water_density": 0.0})
        agg.to_csv(OUTPUT_DIR / "osm_water_features.csv", index=False)
        results["water_agg"] = agg

    # 2. Roads
    r_gdf = results.get("roads")
    if r_gdf is not None and not r_gdf.empty:
        r = r_gdf.to_crs(METRIC_CRS)
        r["length_m"] = r.geometry.length
        j = gpd.sjoin(r, kec_metric, how="inner", predicate="intersects").rename(columns={"name_right": "district"})
        agg = pd.DataFrame({"district": kec_metric["name"].unique()})
        agg = agg.merge(j.groupby("district").size().reset_index(name="road_count"), how="left", on="district")
        agg = agg.merge(j.groupby("district")["length_m"].sum().reset_index(name="road_length_meter"), how="left", on="district")
        for ht in ["primary", "secondary"]:
            sub = j[j.get("highway") == ht]
            agg = agg.merge(sub.groupby("district")["length_m"].sum().reset_index(name=f"{ht}_road_length"), how="left", on="district")
        agg = agg.fillna(0)
        agg["road_length_meter"] = agg["road_length_meter"].round(1)
        agg["primary_road_length"] = agg.get("primary_road_length", 0).round(1)
        agg["secondary_road_length"] = agg.get("secondary_road_length", 0).round(1)
        area_km2 = kec_metric.set_index("name")["area_m2"] / 1e6
        agg["road_density"] = (agg["road_length_meter"] / 1000 / area_km2.reindex(agg["district"]).values).round(3)
        agg.to_csv(OUTPUT_DIR / "osm_transport_features.csv", index=False)
        results["roads_agg"] = agg
    else:
        agg = pd.DataFrame({"district": kec_metric["name"].unique(), "road_count": 0, "road_length_meter": 0.0, "road_density": 0.0, "primary_road_length": 0.0, "secondary_road_length": 0.0})
        agg.to_csv(OUTPUT_DIR / "osm_transport_features.csv", index=False)
        results["roads_agg"] = agg

    # 3. Facilities
    f_gdf = results.get("facilities")
    if f_gdf is not None and not f_gdf.empty:
        f = f_gdf.to_crs(METRIC_CRS)
        j = gpd.sjoin(f, kec_metric, how="inner", predicate="intersects").rename(columns={"name_right": "district"})
        agg = pd.DataFrame({"district": kec_metric["name"].unique()})
        for typ in ["hospital", "clinic", "school", "university", "government"]:
            cnt = j[j.get("amenity") == typ].groupby("district").size().reset_index(name=f"{typ}_count")
            agg = agg.merge(cnt, how="left", on="district")
        agg = agg.fillna(0)
        total = j.groupby("district").size().reset_index(name="public_facility_count")
        agg = agg.merge(total, how="left", on="district").fillna(0)
        area_km2 = kec_metric.set_index("name")["area_m2"] / 1e6
        agg["facility_density"] = (agg["public_facility_count"] / area_km2.reindex(agg["district"]).values).round(3)
        agg.to_csv(OUTPUT_DIR / "osm_facility_features.csv", index=False)
        results["facilities_agg"] = agg
    else:
        agg = pd.DataFrame({"district": kec_metric["name"].unique(), "hospital_count": 0, "clinic_count": 0, "school_count": 0, "university_count": 0, "government_count": 0, "public_facility_count": 0, "facility_density": 0.0})
        agg.to_csv(OUTPUT_DIR / "osm_facility_features.csv", index=False)
        results["facilities_agg"] = agg

    # 4. Buildings
    b_gdf = results.get("buildings")
    if b_gdf is not None and not b_gdf.empty:
        b = b_gdf.to_crs(METRIC_CRS)
        j = gpd.sjoin(b, kec_metric, how="inner", predicate="intersects").rename(columns={"name_right": "district"})
        agg = pd.DataFrame({"district": kec_metric["name"].unique()})
        agg = agg.merge(j.groupby("district").size().reset_index(name="building_count"), how="left", on="district")
        for typ in ["residential", "commercial"]:
            cnt = j[j.get("building") == typ].groupby("district").size().reset_index(name=f"{typ}_count")
            agg = agg.merge(cnt, how="left", on="district")
        agg = agg.fillna(0)
        area_km2 = kec_metric.set_index("name")["area_m2"] / 1e6
        agg["building_density"] = (agg["building_count"] / area_km2.reindex(agg["district"]).values).round(2)
        agg.to_csv(OUTPUT_DIR / "osm_building_features.csv", index=False)
        results["buildings_agg"] = agg
    else:
        agg = pd.DataFrame({"district": kec_metric["name"].unique(), "building_count": 0, "residential_count": 0, "commercial_count": 0, "building_density": 0.0})
        agg.to_csv(OUTPUT_DIR / "osm_building_features.csv", index=False)
        results["buildings_agg"] = agg

    # 5. Environment
    e_gdf = results.get("environment")
    if e_gdf is not None and not e_gdf.empty:
        e = e_gdf.to_crs(METRIC_CRS)
        e_poly = e[e.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
        if not e_poly.empty:
            e_poly["area_m2"] = e_poly.geometry.area
            j = gpd.sjoin(e_poly, kec_metric, how="inner", predicate="intersects").rename(columns={"name_right": "district"})
            green = j[j.get("natural").isin(["wood", "wetland"])].groupby("district")["area_m2"].sum().reset_index(name="green_area_m2")
            water = j[j.get("natural") == "water"].groupby("district")["area_m2"].sum().reset_index(name="water_area_m2")
        else:
            green = pd.DataFrame(columns=["district", "green_area_m2"])
            water = pd.DataFrame(columns=["district", "water_area_m2"])
        agg = pd.DataFrame({"district": kec_metric["name"].unique()})
        agg = agg.merge(green, how="left", on="district").merge(water, how="left", on="district").fillna(0)
        area_m2 = kec_metric.set_index("name")["area_m2"]
        agg["green_ratio"] = (agg["green_area_m2"] / area_m2.reindex(agg["district"]).values).round(6)
        agg["water_ratio"] = (agg["water_area_m2"] / area_m2.reindex(agg["district"]).values).round(6)
        agg.to_csv(OUTPUT_DIR / "osm_environment_features.csv", index=False)
        results["environment_agg"] = agg
    else:
        agg = pd.DataFrame({"district": kec_metric["name"].unique(), "green_area_m2": 0.0, "green_ratio": 0.0, "water_area_m2": 0.0, "water_ratio": 0.0})
        agg.to_csv(OUTPUT_DIR / "osm_environment_features.csv", index=False)
        results["environment_agg"] = agg

    # Final combined CSV
    final = pd.DataFrame({"district": kec_metric["name"].unique()})
    for key in ["water_agg", "roads_agg", "facilities_agg", "buildings_agg", "environment_agg"]:
        if key in results:
            final = final.merge(results[key], how="left", on="district")
    final = final.fillna(0)
    final_path = OUTPUT_DIR / "urban_osm_features_final.csv"
    final.to_csv(final_path, index=False)

    logger.info(f"DONE! Final dataset written to {final_path}")
    logger.info(f"Crawl finished in {time.time()-start:.1f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", type=str, default=TARGET)
    args = parser.parse_args()
    main(args.region)
