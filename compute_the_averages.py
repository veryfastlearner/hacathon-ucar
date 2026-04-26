"""
Extract full THE ranking data for all universities and compute averages.
"""
import urllib.request
import json
import re

url = "https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking"
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

print("Fetching THE rankings page (this may take a minute)...")
try:
    response = urllib.request.urlopen(req, timeout=120)
    html = response.read().decode('utf-8')
except Exception as e:
    print(f"Error fetching URL: {e}")
    exit(1)

print("Parsing HTML...")
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
if not m:
    print("Could not find __NEXT_DATA__ in HTML.")
    exit(1)

next_data = json.loads(m.group(1))

# Find all university entries
def find_universities(obj):
    results = []
    if isinstance(obj, dict):
        if 'name' in obj and 'scores_teaching' in obj:
            results.append(obj)
        for v in obj.values():
            results.extend(find_universities(v))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_universities(item))
    return results

print("Extracting universities...")
unis = find_universities(next_data)
# De-duplicate by name just in case
unique_unis = {}
for u in unis:
    name = u.get('name')
    if name and name not in unique_unis:
        unique_unis[name] = u
unis = list(unique_unis.values())

print(f"Total unique universities found: {len(unis)}")

# Parse scores (some may be "n/a")
def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

teaching_scores = []
research_env_scores = []
research_quality_scores = []
industry_scores = []
international_scores = []

for u in unis:
    t = safe_float(u.get('scores_teaching'))
    r = safe_float(u.get('scores_research'))
    c = safe_float(u.get('scores_citations'))
    i = safe_float(u.get('scores_industry_income'))
    io = safe_float(u.get('scores_international_outlook'))
    
    if t is not None: teaching_scores.append(t)
    if r is not None: research_env_scores.append(r)
    if c is not None: research_quality_scores.append(c)
    if i is not None: industry_scores.append(i)
    if io is not None: international_scores.append(io)

print(f"\n=== Valid scores count ===")
print(f"Teaching:      {len(teaching_scores)} universities")
print(f"Research Env:  {len(research_env_scores)} universities")
print(f"Research Quality: {len(research_quality_scores)} universities")
print(f"Industry:      {len(industry_scores)} universities")
print(f"International: {len(international_scores)} universities")

print(f"\n=== GLOBAL AVERAGES (ALL {len(unis)} universities) ===")
avg_teaching = sum(teaching_scores) / len(teaching_scores) if teaching_scores else 0
avg_research_env = sum(research_env_scores) / len(research_env_scores) if research_env_scores else 0
avg_research_quality = sum(research_quality_scores) / len(research_quality_scores) if research_quality_scores else 0
avg_industry = sum(industry_scores) / len(industry_scores) if industry_scores else 0
avg_international = sum(international_scores) / len(international_scores) if international_scores else 0

print(f"Teaching:           {avg_teaching:.2f}")
print(f"Research Env:       {avg_research_env:.2f}")
print(f"Research Quality:   {avg_research_quality:.2f}")
print(f"Industry:           {avg_industry:.2f}")
print(f"International:      {avg_international:.2f}")

# Save full data for dashboard use
the_global_averages = {
    "total_universities": len(unis),
    "valid_counts": {
        "teaching": len(teaching_scores),
        "research_environment": len(research_env_scores),
        "research_quality": len(research_quality_scores),
        "industry": len(industry_scores),
        "international_outlook": len(international_scores)
    },
    "global_averages": {
        "teaching": round(avg_teaching, 2),
        "research_environment": round(avg_research_env, 2),
        "research_quality": round(avg_research_quality, 2),
        "industry": round(avg_industry, 2),
        "international_outlook": round(avg_international, 2)
    }
}

with open('the_global_averages.json', 'w', encoding='utf-8') as f:
    json.dump(the_global_averages, f, indent=2, ensure_ascii=False)

print(f"\nSaved to the_global_averages.json")
