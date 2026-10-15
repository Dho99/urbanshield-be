import requests, re

r = requests.get('https://download.geofabrik.de/asia/indonesia.html')
print("Status:", r.status_code)
for l in re.findall(r'href="([^"]+\.osm\.pbf)"', r.text):
    print("Found:", l)
