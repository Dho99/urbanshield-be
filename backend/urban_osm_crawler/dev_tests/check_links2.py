import requests, re
r = requests.get('https://download.geofabrik.de/asia/indonesia.html', headers={'User-Agent': 'Mozilla/5.0'})
links = re.findall(r'href="([^"]*\.pbf)"', r.text)
for l in links[:10]:
    full = requests.compat.urljoin('https://download.geofabrik.de/asia/indonesia.html', l)
    h = requests.head(full, headers={'User-Agent': 'Mozilla/5.0'})
    print(l, h.status_code, full)
