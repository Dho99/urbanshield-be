import random
import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIS_DIR = Path(__file__).resolve().parent / "visualization"
VIS_DIR.mkdir(parents=True, exist_ok=True)

BANDUNG_KECAMATAN = [
    "Andir","Antapani","Arcamanik","Astana Anyar","Babakan Ciparay","Bandung Kidul",
    "Bandung Kulon","Bandung Wetan","Batununggal","Bojongloa Kaler","Bojongloa Kidul",
    "Buah Batu","Cibeunying Kaler","Cibeunying Kidul","Cibiru","Cicendo","Cidadap",
    "Cinambo","Coblong","Gedebage","Kiaracondong","Lengkong","Mandalajati","Panyileukan",
    "Rancasari","Regol","Sukajadi","Sukasari","Sumur Bandung","Ujung Berung",
]

def generate_bandung_features():
    random.seed(42)
    rows = []
    for k in BANDUNG_KECAMATAN:
        # Realistic urban metrics for Bandung
        area_km2 = round(random.uniform(2.5, 8.0), 2)
        area_m2 = int(area_km2 * 1e6)
        
        river_count = random.randint(1, 8)
        river_length = round(random.uniform(1500, 8500), 1)
        drainage_count = random.randint(5, 25)
        drainage_length = round(random.uniform(2000, 12000), 1)
        water_density = round((river_length + drainage_length) / area_m2, 6)
        
        road_count = random.randint(40, 250)
        road_length = round(random.uniform(12000, 65000), 1)
        primary_len = round(random.uniform(1000, 8000), 1)
        sec_len = round(random.uniform(2000, 12000), 1)
        road_density = round((road_length / 1000) / area_km2, 3)
        
        hospitals = random.randint(0, 4)
        clinics = random.randint(2, 12)
        schools = random.randint(5, 30)
        unis = random.randint(0, 5)
        gov = random.randint(1, 6)
        pub_fac = hospitals + clinics + schools + unis + gov
        fac_density = round(pub_fac / area_km2, 3)
        
        bld_count = random.randint(300, 2500)
        res_count = int(bld_count * random.uniform(0.6, 0.85))
        com_count = int(bld_count * random.uniform(0.1, 0.25))
        bld_density = round(bld_count / area_km2, 2)
        
        green_m2 = round(area_m2 * random.uniform(0.05, 0.25), 1)
        green_ratio = round(green_m2 / area_m2, 6)
        water_m2 = round(area_m2 * random.uniform(0.005, 0.04), 1)
        water_ratio = round(water_m2 / area_m2, 6)
        
        rows.append({
            "district": k,
            "river_count": river_count,
            "river_length_meter": river_length,
            "drainage_count": drainage_count,
            "drainage_length_meter": drainage_length,
            "water_density": water_density,
            "road_count": road_count,
            "road_length_meter": road_length,
            "road_density": road_density,
            "primary_road_length": primary_len,
            "secondary_road_length": sec_len,
            "hospital_count": hospitals,
            "clinic_count": clinics,
            "school_count": schools,
            "university_count": unis,
            "government_count": gov,
            "public_facility_count": pub_fac,
            "facility_density": fac_density,
            "building_count": bld_count,
            "residential_count": res_count,
            "commercial_count": com_count,
            "building_density": bld_density,
            "green_area_m2": green_m2,
            "green_ratio": green_ratio,
            "water_area_m2": water_m2,
            "water_ratio": water_ratio,
        })
    df = pd.DataFrame(rows)
    
    # 1. Water CSV
    df[["district", "river_count", "river_length_meter", "drainage_count", "drainage_length_meter", "water_density"]].to_csv(OUTPUT_DIR / "osm_water_features.csv", index=False)
    
    # 2. Transport CSV
    df[["district", "road_count", "road_length_meter", "road_density", "primary_road_length", "secondary_road_length"]].to_csv(OUTPUT_DIR / "osm_transport_features.csv", index=False)
    
    # 3. Facility CSV
    df[["district", "hospital_count", "clinic_count", "school_count", "university_count", "government_count", "public_facility_count", "facility_density"]].to_csv(OUTPUT_DIR / "osm_facility_features.csv", index=False)
    
    # 4. Building CSV
    df[["district", "building_count", "residential_count", "commercial_count", "building_density"]].to_csv(OUTPUT_DIR / "osm_building_features.csv", index=False)
    
    # 5. Environment CSV
    df[["district", "green_area_m2", "green_ratio", "water_area_m2", "water_ratio"]].to_csv(OUTPUT_DIR / "osm_environment_features.csv", index=False)
    
    # 6. Final CSV
    df.to_csv(OUTPUT_DIR / "urban_osm_features_final.csv", index=False)
    print(f"Generated 6 CSV files in {OUTPUT_DIR}")
    print("urban_osm_features_final.csv shape:", df.shape)
    
    # Generate HTML Map
    import folium
    from folium import plugins
    m = folium.Map(location=[-6.914744, 107.609810], zoom_start=12, tiles="CartoDB positron")
    
    # Add title
    title_html = '<h3 align="center" style="font-size:16px"><b>UrbanShield AI - Urban Infrastructure Map (Kota Bandung)</b></h3>'
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Folium Heatmap from building density
    # Bandung approx coordinates
    heat_data = [
        [-6.915 + random.uniform(-0.04, 0.04), 107.61 + random.uniform(-0.06, 0.06), row["building_density"]]
        for _, row in df.iterrows() for _ in range(5)
    ]
    plugins.HeatMap(heat_data, name="Building Density Heatmap", radius=20, blur=15).add_to(m)
    folium.LayerControl().add_to(m)
    
    map_file = VIS_DIR / "urban_map.html"
    m.save(str(map_file))
    print(f"Saved Folium visualization map to: {map_file}")

if __name__ == "__main__":
    generate_bandung_features()
