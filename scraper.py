import urllib.request
import re
import json

url = 'https://www.timeshighereducation.com/world-university-rankings/university-carthage'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')

with open('page.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved page to page.html")
