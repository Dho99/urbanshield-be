import requests
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, shape
from .config import BOUNDARY_DIR, NOMINATIM_UA
from .overpass.client import overpass_json
from .overpass.queries import kecamatan_query


def nominatim_polygon(query: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "polygon_geojson": 1, "limit": 1}
    r = requests.get(url, params=params, headers={"User-Agent": NOMINATIM_UA}, timeout=30)
    r.raise_for_status()
    j = r.json()
    if not j:
        raise ValueError(f"region not found: {query}")
    gj = j[0].get("geojson")
    if not gj:
        raise ValueError(f"no polygon for: {query}")
    geom = shape(gj)
    if geom.geom_type == "Polygon":
        geom = MultiPolygon([geom])
    props = {"name": j[0].get("display_name",""), "osm_id": j[0].get("osm_id"), "admin_level": 7, "parent_region": query}
    gdf = gpd.GeoDataFrame([props], geometry=[geom], crs=4326)
    return gdf


def city_boundary(query="Kota Bandung, Jawa Barat, Indonesia"):
    try:
        gdf = nominatim_polygon(query)
    except Exception:
        try:
            import osmnx as ox
            gdf = ox.geocode_to_gdf(query).to_crs(4326)
            if gdf.geometry.iloc[0].geom_type == "Polygon":
                gdf.geometry = gdf.geometry.apply(lambda g: MultiPolygon([g]))
        except Exception as e:
            raise RuntimeError(f"geocode fail {query}: {e}")
    gdf.to_file(BOUNDARY_DIR / "city.geojson", driver="GeoJSON")
    return gdf


def kecamatan_boundaries(city_query="Kota Bandung, Jawa Barat, Indonesia"):
    data = overpass_json(kecamatan_query())
    feats = []
    for el in data.get("elements", []):
        if el["type"] != "relation":
            continue
        tags = el.get("tags", {})
        name = tags.get("name", f"rel-{el['id']}")
        polys = []
        for m in el.get("members", []):
            if m.get("role") in ("outer", "") and m.get("geometry"):
                c = [(p["lon"], p["lat"]) for p in m["geometry"]]
                if len(c) >= 4:
                    try:
                        polys.append(Polygon(c))
                    except Exception:
                        continue
        if not polys:
            continue
        geom = MultiPolygon(polys) if len(polys) > 1 else polys[0]
        if not geom.is_valid:
            geom = geom.buffer(0)
        feats.append({"name": name, "osm_id": el["id"], "admin_level": 8, "parent_region": city_query, "geometry": geom})
    if not feats:
        raise RuntimeError("no kecamatan found via Overpass")
    gdf = gpd.GeoDataFrame(feats, crs=4326).drop_duplicates("name").sort_values("name").reset_index(drop=True)
    gdf.to_file(BOUNDARY_DIR / "kecamatan.geojson", driver="GeoJSON")
    return gdf
