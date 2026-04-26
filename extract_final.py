import json
from datetime import datetime

data_file = 'wurRankingsGRAData.json'
with open(data_file, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Sort raw_data by year
raw_data.sort(key=lambda x: x.get('year', 0))

categories_map = {
    'Overall': 'world',
    'Business and Economics': 'business_economics',
    'Computer Science': 'computer_science',
    'Engineering': 'engineering',
    'Life Sciences': 'life_sciences'
}

score_keys = {
    'Teaching': 'teaching',
    'Research Environment': 'research_environment',
    'Research Quality': 'research_quality',
    'Industry': 'industry',
    'International Outlook': 'international_outlook',
    'Research': 'research_environment', # Handling older names if needed
    'Citations': 'research_quality',
}

rankings = {
    cat_id: {"rank": "", "scores": {}, "trend": []}
    for cat_id in categories_map.values()
}

for year_data in raw_data:
    year = year_data.get('year')
    level1s = year_data.get('level1s', [])
    for l1 in level1s:
        name = l1.get('name')
        if name not in categories_map:
            continue
        cat_id = categories_map[name]
        
        # trend teaching score
        level2s = l1.get('level2s', [])
        teaching_score = None
        scores_dict = {}
        for l2 in level2s:
            metric_name = l2.get('name')
            score = l2.get('result', {}).get('score')
            if score is not None:
                if metric_name == 'Teaching':
                    teaching_score = score
                if metric_name in score_keys:
                    scores_dict[score_keys[metric_name]] = score
        
        if teaching_score is not None:
            rankings[cat_id]['trend'].append({
                "year": year,
                "teaching_score": teaching_score
            })
            
        if year == 2026:
            rankings[cat_id]['scores'] = scores_dict
            rank = l1.get('result', {}).get('rank', {}).get('displayRank', '')
            rankings[cat_id]['rank'] = rank.replace('\u2013', '-')

# Calculate AI Insights
def parse_rank(rstr):
    if not rstr: return 9999
    rstr = str(rstr).replace('+', '').replace('\u2013', '-')
    if '-' in rstr:
        parts = rstr.split('-')
        return (int(parts[0]) + int(parts[1])) / 2
    return int(rstr)

best_rank_val = 9999
best_cat = None
for name, cat_id in categories_map.items():
    r = parse_rank(rankings[cat_id]['rank'])
    if r < best_rank_val:
        best_rank_val = r
        best_cat = name

weakest_score_val = 999
weakest_score_name = None
for cat_id, data in rankings.items():
    if not data['scores']: continue
    for k, v in data['scores'].items():
        if v < weakest_score_val:
            weakest_score_val = v
            weakest_score_name = f"{k} in {cat_id}"

fastest_improving_val = -999
fastest_improving = None
for name, cat_id in categories_map.items():
    tr = rankings[cat_id]['trend']
    if len(tr) >= 2:
        diff = tr[-1]['teaching_score'] - tr[0]['teaching_score']
        if diff > fastest_improving_val:
            fastest_improving_val = diff
            fastest_improving = name

ai_insights = {
    "strongest_category": best_cat,
    "weakest_score": weakest_score_name,
    "fastest_improving": fastest_improving,
    "recommended_priority": f"Renforcer les initiatives de {weakest_score_name} pour améliorer le classement global."
}

final_output = {
  "university": "University of Carthage",
  "country": "Tunisia",
  "scraped_at": "2026-04-25",
  "rankings": rankings,
  "ai_insights": ai_insights
}

with open('extracted_ranking_data.json', 'w', encoding='utf-8') as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print("Saved to extracted_ranking_data.json")
