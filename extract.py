import re
import json

with open('page.html', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if m:
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(json.loads(m.group(1)), f, indent=2)
    print("Extracted to data.json")
else:
    print("Could not find __NEXT_DATA__")
