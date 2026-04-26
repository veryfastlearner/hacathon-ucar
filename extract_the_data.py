#!/usr/bin/env python3
"""Quick script to extract THE ranking data from Next.js SSR - overview page"""
import requests, re, json

url = 'https://www.timeshighereducation.com/world-university-rankings/university-carthage'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
if match:
    data = json.loads(match.group(1))
    props = data.get('props', {}).get('pageProps', {})
    view_props = props.get('viewProps', {})
    
    # 1. WUR Rankings (GRA data)
    gra = view_props.get('wurRankingsGRAData', [])
    print("=== WUR RANKINGS (GRA DATA) ===")
    print(json.dumps(gra, indent=2)[:5000])
    
    # 2. Subject Rankings
    subjects = view_props.get('subjectsGRAData', {})
    print("\n=== SUBJECT RANKINGS ===")
    print(json.dumps(subjects, indent=2)[:5000])
    
    # 3. Key Stats
    stats = view_props.get('keyStatsGRAData', [])
    print("\n=== KEY STUDENT STATS ===")
    print(json.dumps(stats, indent=2)[:5000])
    
    # 4. Impact Rankings
    impact = view_props.get('impactRankingsGRAData', [])
    print("\n=== IMPACT RANKINGS ===")
    print(json.dumps(impact, indent=2)[:3000])
    
    # 5. Header info
    header = props.get('headerProps', {})
    print("\n=== HEADER INFO ===")
    print(json.dumps(header, indent=2)[:2000])
    
    # 6. Dump ALL viewProps keys for reference
    print("\n=== ALL viewProps KEYS ===")
    print(list(view_props.keys()))
else:
    print("No __NEXT_DATA__ found")
