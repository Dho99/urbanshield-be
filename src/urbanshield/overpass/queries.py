FILTERS = {
    "osm_waterways": 'nwr["waterway"~"canal|river|stream|drain|ditch"]',
    "osm_roads": 'nwr["highway"]',
    "osm_facilities": 'nwr["amenity"~"school|university|college|hospital|clinic|doctors|community_centre|townhall|marketplace|police|fire_station"]',
    "osm_buildings": 'nwr["building"]',
    "osm_landuse": 'nwr["landuse"]',
}

FASUM_SUB = {
    "sekolah": ["school","university","college"],
    "rs": ["hospital","clinic","doctors"],
}

def poly_str(geom):
    if geom.geom_type == "Polygon":
        coords = list(geom.exterior.coords)
    elif geom.geom_type == "MultiPolygon":
        coords = list(geom.geoms[0].exterior.coords)
    else:
        coords = list(geom.envelope.exterior.coords)
    return " ".join(f"{y} {x}" for x,y in coords)

def build_query(poly_wkt_geom, table_key):
    filt = FILTERS[table_key]
    poly = poly_str(poly_wkt_geom)
    return f'[out:json][timeout:90];({filt}(poly:"{poly}"););out geom;'

def kecamatan_query():
    return '[out:json][timeout:90];rel["boundary"="administrative"]["admin_level"="7"]["name"~"Bandung",i]->.city;map_to_area .city->.a;(rel["boundary"="administrative"]["admin_level"="8"](area.a););out geom;'
