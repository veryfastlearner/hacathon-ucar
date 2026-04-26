"""
Scrape THE World University Rankings data for 2000+ universities.
Strategy: Use the __NEXT_DATA__ payload which contains the ranking table config,
then find the GraphQL/API endpoint used to load more rows.
If that fails, iterate through individual university pages.
"""
import urllib.request
import json
import re
import time

def try_api_approach():
    """Try to find the THE API endpoint from the page source."""
    url = "https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking"
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
    
    # Look for any API/data URLs
    # Pattern 1: Look for ranking data endpoint in script tags
    all_urls = re.findall(r'https?://[^\s\"\'\<\>]+', html)
    data_urls = [u for u in all_urls if 'ranking' in u.lower() and ('json' in u.lower() or 'api' in u.lower() or 'data' in u.lower())]
    
    print("=== Potential data URLs found ===")
    for u in set(data_urls):
        print(u)
    
    # Pattern 2: Look for GraphQL endpoint
    graphql = [u for u in all_urls if 'graphql' in u.lower()]
    print("\n=== GraphQL URLs ===")
    for u in set(graphql):
        print(u)
    
    # Pattern 3: Check __NEXT_DATA__ for API config
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if m:
        next_data = json.loads(m.group(1))
        # Find any "api" or "endpoint" keys
        def find_keys(obj, target_keys, path=""):
            results = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(t in k.lower() for t in target_keys):
                        results.append((path + "." + k, v))
                    results.extend(find_keys(v, target_keys, path + "." + k))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    results.extend(find_keys(item, target_keys, path + f"[{i}]"))
            return results
        
        api_keys = find_keys(next_data, ['api', 'endpoint', 'url', 'graphql', 'data_source', 'ranking'])
        print("\n=== Keys containing 'api/endpoint/url/graphql/ranking' in __NEXT_DATA__ ===")
        for path, val in api_keys[:30]:
            if isinstance(val, str) and len(val) < 200:
                print(f"  {path}: {val}")
            elif isinstance(val, str):
                print(f"  {path}: {val[:100]}...")
                
    return html

def try_direct_scrape(html):
    """Try to extract ranking data directly from the page HTML."""
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not m:
        return None
    
    next_data = json.loads(m.group(1))
    
    # Look for ranking table data
    def find_universities(obj, path=""):
        results = []
        if isinstance(obj, dict):
            # Check if this dict looks like a university entry
            if 'name' in obj and ('scores_teaching' in obj or 'teaching' in obj or 'rank' in obj):
                results.append(obj)
            for k, v in obj.items():
                results.extend(find_universities(v, path + "." + k))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                results.extend(find_universities(item, path + f"[{i}]"))
        return results
    
    unis = find_universities(next_data)
    print(f"\n=== Universities found in __NEXT_DATA__: {len(unis)} ===")
    if unis:
        print("Sample:", json.dumps(unis[0], indent=2)[:500])
    return unis

html = try_api_approach()
try_direct_scrape(html)
