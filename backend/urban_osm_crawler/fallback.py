import geopandas as gpd
from shapely.geometry import box
BANDUNG_KECAMATAN = [
    "Andir","Antapani","Arcamanik","Astana Anyar","Babakan Ciparay","Bandung Kidul",
    "Bandung Kulon","Bandung Wetan","Batununggal","Bojongloa Kaler","Bojongloa Kidul",
    "Buah Batu","Cibeunying Kaler","Cibeunying Kidul","Cibiru","Cicendo","Cidadap",
    "Cinambo","Coblong","Gedebage","Kiaracondong","Lengkong","Mandalajati","Panyileukan",
    "Rancasari","Regol","Sukajadi","Sukasari","Sumur Bandung","Ujung Berung",
]
def make_fallback_kecamatan(city_gdf, crs_metric="EPSG:32748"):
    import numpy as np
    wgs = city_gdf.to_crs("EPSG:4326")
    minx, miny, maxx, maxy = wgs.total_bounds
    cols, rows = 6, 5
    dx = (maxx - minx) / cols
    dy = (maxy - miny) / rows
    feats = []
    idx = 0
    for r in range(rows):
        for c in range(cols):
            if idx >= len(BANDUNG_KECAMATAN): break
            geom = box(minx + c*dx, miny + r*dy, minx + (c+1)*dx, miny + (r+1)*dy)
            feats.append({"name": BANDUNG_KECAMATAN[idx], "geometry": geom, "admin_level": 8, "osm_id": 900000+idx})
            idx += 1
    gdf = gpd.GeoDataFrame(feats, crs="EPSG:4326").to_crs(crs_metric)
    gdf["area_m2"] = gdf.geometry.area
    return gdf
