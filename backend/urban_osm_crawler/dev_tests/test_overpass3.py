import requests
url = "https://overpass.osm.ch/api/interpreter"
q = '[out:json][timeout:60];rel["boundary"="administrative"]["name"~"Bandung",i];out tags;'
r = requests.post(url, data={"data": q}, headers={"User-Agent": "UrbanShieldAI/1.0"}, timeout=60)
print(r.status_code)
j = r.json()
for el in j.get("elements", []):
    print(el.get("id"), el.get("tags", {}).get("admin_level"), el.get("tags", {}).get("name"))
