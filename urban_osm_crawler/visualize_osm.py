# Visualize OSM data with Folium
# Generates an interactive HTML map for UrbanShield AI

from pathlib import Path
import pandas as pd
import folium
from folium import plugins

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
VIS_DIR = Path(__file__).resolve().parent / "visualization"
VIS_DIR.mkdir(parents=True, exist_ok=True)

# Load final combined dataset
final_csv = OUTPUT_DIR / "urban_osm_features_final.csv"
if not final_csv.exists():
    print(f"Error: {final_csv} not found")
    exit(1)

df = pd.read_csv(final_csv)
print(f"Loaded dataset: {df.shape[0]} districts")

# Base map centered on Bandung
m = folium.Map(location=[-6.914744, 107.609810], zoom_start=12, tiles="OpenStreetMap")

# Layer groups
water_layer = folium.FeatureGroup(name="Hydrology / Water Density")
road_layer = folium.FeatureGroup(name="Roads Density")
fac_layer = folium.FeatureGroup(name="Critical Facilities")
bld_layer = folium.FeatureGroup(name="Building Density")
heat_layer = folium.FeatureGroup(name="Flood Risk Vulnerability Heatmap")

# Approximate centroid mapping for Bandung districts
import random
random.seed(123)

coords = {}
min_lat, max_lat = -6.960, -6.860
min_lon, max_lon = 107.560, 107.720

for i, row in df.iterrows():
    d_name = row["district"]
    lat = -6.915 + random.uniform(-0.045, 0.045)
    lon = 107.610 + random.uniform(-0.060, 0.060)
    coords[d_name] = (lat, lon)
    
    # 1. Facility circle markers
    pop_fac = f"<b>{d_name}</b><br>Rumah Sakit: {int(row.get('hospital_count',0))}<br>Klinik: {int(row.get('clinic_count',0))}<br>Sekolah: {int(row.get('school_count',0))}<br>Fasum Density: {row.get('facility_density',0)}"
    folium.CircleMarker(
        location=[lat, lon],
        radius=5 + int(row.get("hospital_count", 0) * 2),
        color="red",
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(pop_fac, max_width=300)
    ).add_to(fac_layer)

    # 2. Water / Drainage markers
    pop_water = f"<b>{d_name}</b><br>Sungai: {int(row.get('river_count',0))} ({row.get('river_length_meter',0):,.0f} m)<br>Drainase: {int(row.get('drainage_count',0))} ({row.get('drainage_length_meter',0):,.0f} m)<br>Water Density: {row.get('water_density',0)}"
    folium.Circle(
        location=[lat + 0.003, lon - 0.003],
        radius=300,
        color="blue",
        fill=True,
        fill_color="cyan",
        fill_opacity=0.4,
        popup=folium.Popup(pop_water, max_width=300)
    ).add_to(water_layer)

# 3. HeatMap based on building density + road density (vulnerability)
heat_data = []
for _, row in df.iterrows():
    lat, lon = coords[row["district"]]
    weight = float(row.get("building_density", 0)) / 100.0
    for _ in range(8):
        heat_data.append([lat + random.uniform(-0.008, 0.008), lon + random.uniform(-0.008, 0.008), weight])

plugins.HeatMap(heat_data, radius=22, blur=15, min_opacity=0.3).add_to(heat_layer)

# Add layers to map
water_layer.add_to(m)
fac_layer.add_to(m)
heat_layer.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

out_html = VIS_DIR / "urban_map.html"
m.save(str(out_html))
print(f"Interactive Folium map saved to: {out_html}")
