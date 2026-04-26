#!/usr/bin/env python3
import requests, re, json

r = requests.get('https://www.timeshighereducation.com/world-university-rankings/university-carthage', headers={'User-Agent':'Mozilla/5.0'})
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
data = json.loads(match.group(1))
props = data['props']['pageProps']['viewProps']

gra = props.get('wurRankingsGRAData', [])
print('WUR releases:', len(gra))
for release in gra:
    name = release.get('name')
    year = release.get('year')
    print('\nRelease:', name, '(year', year, ')')
    for l1 in release.get('level1s', []):
        l1_name = l1.get('name')
        l1_key = l1.get('key')
        print('  L1:', l1_name, 'key=', l1_key)
        l2s = l1.get('level2s')
        if l2s:
            print('    L2 count:', len(l2s))
            for l2 in l2s:
                l2_name = l2.get('name')
                score = l2.get('result', {}).get('score')
                print('      ', l2_name, ': score=', score)
        else:
            print('    L2: null')
