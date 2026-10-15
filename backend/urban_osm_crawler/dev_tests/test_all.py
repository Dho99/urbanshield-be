import requests
mirrors = [
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
tests = {
    "node_count": '[out:json][timeout:25];node(-6.92,107.60,-6.91,107.61);out count;',
    "way_hw_small": '[out:json][timeout:25];way["highway"](-6.915,107.605,-6.914,107.610);out tags 5;',
    "way_hw_med": '[out:json][timeout:25];way["highway"~"primary|secondary"](-6.95,107.59,-6.90,107.63);out tags 5;',
    "nwr_water": '[out:json][timeout:25];nwr["waterway"](-6.95,107.59,-6.90,107.63);out tags 5;',
}
headers = {"User-Agent": "UrbanShieldAI/1.0"}
for name, q in tests.items():
    print(f"\n=== {name} ===")
    print("Q:", q[:100])
    for url in mirrors:
        try:
            r = requests.post(url, data={"data": q}, headers=headers, timeout=30)
            print(url, r.status_code, len(r.text))
            if r.status_code == 200:
                try:
                    j = r.json()
                    els = j.get("elements", [])
                    print("  elements:", len(els), str(els[:1])[:200] if els else "")
                except Exception as e:
                    print("  json err", e, r.text[:200])
            else:
                print("  body:", r.text[:200])
        except Exception as e:
            print(url, "ERR", str(e)[:150])
