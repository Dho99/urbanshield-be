import requests
url = "https://overpass.osm.ch/api/interpreter"
q = '[out:json][timeout:60];area["name"="Bandung"]["boundary"="administrative"]->.a;(rel["boundary"="administrative"]["admin_level"="8"](area.a););out geom;'
r = requests.post(url, data={"data": q}, headers={"User-Agent": "UrbanShieldAI/1.0"}, timeout=60)
print(r.status_code, len(r.text))
j = r.json()
print("elements:", len(j.get("elements", [])))
print([e.get("tags", {}).get("name") for e in j.get("elements", []) if e.get("type") == "relation"][:10])
