import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon


def elements_to_gdf(data: dict, table_key: str):
    rows = []
    for el in data.get("elements", []):
        t = el.get("type")
        tags = el.get("tags", {}) or {}
        osm_id = el.get("id")
        geom = None
        try:
            if t == "node":
                geom = Point(el["lon"], el["lat"])
            elif t == "way":
                g = el.get("geometry", [])
                coords = [(p["lon"], p["lat"]) for p in g]
                if len(coords) < 2:
                    continue
                if coords[0] == coords[-1] and len(coords) >= 4 and (table_key in ("osm_buildings", "osm_landuse") or "building" in tags):
                    geom = Polygon(coords)
                else:
                    geom = LineString(coords)
            else:
                continue
        except Exception:
            continue
        if geom is None or geom.is_empty:
            continue
        row = {
            "osm_id": osm_id,
            "osm_type": t,
            "name": tags.get("name"),
            "tags": json.dumps(tags, ensure_ascii=False),
            "geometry": geom,
        }
        if table_key == "osm_waterways":
            row["waterway"] = tags.get("waterway")
        elif table_key == "osm_roads":
            row["highway"] = tags.get("highway")
        elif table_key == "osm_facilities":
            amenity = tags.get("amenity")
            row["amenity"] = amenity
            a = (amenity or "").lower()
            if a in ("school", "university", "college"):
                row["category"] = "sekolah"
            elif a in ("hospital", "clinic", "doctors"):
                row["category"] = "rs"
            else:
                row["category"] = "fasum"
        elif table_key == "osm_buildings":
            row["building"] = tags.get("building")
        elif table_key == "osm_landuse":
            row["landuse"] = tags.get("landuse")
        rows.append(row)
    if not rows:
        return gpd.GeoDataFrame(columns=["osm_id", "geometry"], crs=4326)
    gdf = gpd.GeoDataFrame(rows, crs=4326)
    gdf = gdf[gdf.geometry.notnull()].reset_index(drop=True)
    return gdf
