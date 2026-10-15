import requests
mirrors = [
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
q = '[out:json][timeout:60];(rel["boundary"="administrative"]["admin_level"="8"](-6.97,107.54,-6.83,107.74););out geom;'
headers = {"User-Agent": "UrbanShieldAI/1.0"}
for url in mirrors:
    try:
        print("TRY", url)
        r = requests.post(url, data={"data": q}, headers=headers, timeout=70)
        print(url, r.status_code, len(r.text))
        if r.status_code == 200:
            j = r.json()
            print("elements", len(j.get("elements", [])))
            names = [e.get("tags", {}).get("name") for e in j.get("elements", [])[:10]]
            print(names)
            break
    except Exception as e:
        print(url, "ERR", e)
