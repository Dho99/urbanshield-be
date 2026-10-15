import requests, json

headers = {
    "User-Agent": "UrbanShieldAI/1.0 (info@urbanshield.ai; research project)",
    "Referer": "https://github.com/urbanshield-ai"
}

servers = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

tests = [
    ("tile_highway", '[out:json][timeout:30];way["highway"](-6.92,107.60,-6.90,107.63);out geom 50;'),
    ("area_waterway", '[out:json][timeout:30];area["name"="Bandung"]["boundary"="administrative"]->.a;nwr["waterway"](area.a);out count;'),
    ("kecamatan_rel", '[out:json][timeout:30];area["name"="Bandung"]["boundary"="administrative"]->.a;rel["boundary"="administrative"]["admin_level"="8"](area.a);out tags;'),
]

for name, q in tests:
    print(f"\n=== {name} ===")
    for s in servers:
        try:
            r = requests.post(s, data={"data": q}, headers=headers, timeout=35)
            print(f"[{s}] status={r.status_code}")
            if r.status_code == 200:
                j = r.json()
                els = j.get("elements", [])
                print(f"  elements count: {len(els)}")
                if els and "tags" in els[0]:
                    print("  sample tag:", list(els[0]["tags"].items())[:2])
                elif els and "count" in els[0]:
                    print("  count result:", els[0]["count"])
                break
        except Exception as e:
            print(f"[{s}] ERR: {e}")
