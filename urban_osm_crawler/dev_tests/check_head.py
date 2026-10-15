import requests
url = 'https://download.geofabrik.de/asia/indonesia-latest.osm.pbf'
r = requests.head(url, headers={'User-Agent': 'UrbanShieldAI/1.0'}, allow_redirects=True, timeout=15)
print('Status:', r.status_code)
print('Size (MB):', int(r.headers.get('Content-Length', 0))/1e6)
