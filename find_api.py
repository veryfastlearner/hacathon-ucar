import urllib.request
import re
import json

url = "https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8')

# The page data usually contains a datatable URL
# Sometimes it's embedded in NEXT_DATA, let's look inside NEXT_DATA for ".json"
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
if m:
    next_data = json.loads(m.group(1))
    
    # Recursively find any string ending in .json
    def find_json_urls(obj):
        urls = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                urls.extend(find_json_urls(v))
        elif isinstance(obj, list):
            for item in obj:
                urls.extend(find_json_urls(item))
        elif isinstance(obj, str) and ".json" in obj and "world_university_rankings" in obj:
            urls.append(obj)
        return urls

    found = find_json_urls(next_data)
    print("Found JSON URLs:")
    for f in set(found):
        print(f)
else:
    print("NEXT_DATA not found.")
