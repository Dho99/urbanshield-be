import requests
url = "https://overpass.osm.ch/api/interpreter"
# south,west,north,east: -6.97, 107.54, -6.83, 107.74
q = '[out:json][timeout:25];(way["highway"](-6.95,107.59,-6.90,107.63););out geom 50;'
r = requests.post(url, data={"data": q}, headers={"User-Agent": "UrbanShieldAI/1.0"}, timeout=30)
print(r.status_code, len(r.json().get("elements", [])))
