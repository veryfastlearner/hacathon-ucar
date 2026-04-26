import urllib.request
import json
import re

url = "https://www.timeshighereducation.com/world-university-rankings/2024/world-ranking"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    # Find the JSON data URL that THE uses for its datatable
    m = re.search(r'\"(https://www.timeshighereducation.com/sites/default/files/the_data_rankings/.*?\.json)\"', html)
    if m:
        data_url = m.group(1).replace('\\/', '/')
        print(f"Found data URL: {data_url}")
        
        # Fetch the JSON
        data_req = urllib.request.Request(data_url, headers={'User-Agent': 'Mozilla/5.0'})
        json_data = json.loads(urllib.request.urlopen(data_req).read().decode('utf-8'))
        
        print(f"Total universities found: {len(json_data.get('data', []))}")
        with open('the_full_ranking.json', 'w') as f:
            json.dump(json_data, f)
    else:
        print("Data URL not found in HTML.")
except Exception as e:
    print(f"Error: {e}")
