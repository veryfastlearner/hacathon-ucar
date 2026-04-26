import urllib.request
import re

url = "https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8')

# Search for the GraphQL API or the _next/data/ URI
m = re.findall(r'"/(_next/data/[^"]+\.json[^"]*)"', html)
if m:
    print("Found next data endpoints:")
    for url in set(m):
        print(f"https://www.timeshighereducation.com{url}")
else:
    print("No next data urls found.")
