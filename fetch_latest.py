import urllib.request
import json
import re

url = "https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if m:
        data = json.loads(m.group(1))
        # Navigate props to find data
        print(data['props']['pageProps'].keys())
        with open('latest_ranking.json', 'w') as f:
            json.dump(data, f)
    else:
        print("NEXT_DATA not found.")
except Exception as e:
    print(f"Error: {e}")
