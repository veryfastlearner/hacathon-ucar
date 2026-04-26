#!/usr/bin/env python3
"""Extract rankingsVisualisation and about data from THE"""
import requests, re, json

url = 'https://www.timeshighereducation.com/world-university-rankings/university-carthage'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
if match:
    data = json.loads(match.group(1))
    props = data.get('props', {}).get('pageProps', {})
    view_props = props.get('viewProps', {})
    
    # rankingsVisualisation - likely has pillar scores
    rv = view_props.get('rankingsVisualisation', {})
    print("=== RANKINGS VISUALISATION ===")
    print(json.dumps(rv, indent=2)[:8000])
    
    # about section
    about = view_props.get('about', {})
    print("\n=== ABOUT ===")
    print(json.dumps(about, indent=2)[:3000])
    
    # subjects
    subjects = view_props.get('subjects', {})
    print("\n=== SUBJECTS ===")
    print(json.dumps(subjects, indent=2)[:3000])
else:
    print("No __NEXT_DATA__ found")
