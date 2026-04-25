import re

full_text = """1. Informations générales du document ... (truncated for regex)
Budget du MESRS	1762,591	1874,268	1997	2153	2277,238	2293,393
Total étudiants inscrits public + privé	269424	270430	298805	305918	315184	324564
Pourcentage secteur privé	13,1%	14,0%	14,1%	14,7%	15,3%	15,9%
Nombre d’étudiants étrangers	8234	8315	9498	9047	8062
Nombre de foyers universitaires	108	105	121	120	120	130
Nombre de laboratoires de recherche	484	490	501	526
Nombre d’enseignants chercheurs	12679	13061	12740	13919
"""

fields = {}

m_budget = re.findall(r'Budget du MESRS.*?([\d,]+)', full_text)
if m_budget: fields['budget_mesrs_millions'] = float(m_budget[-1].replace(',', '.'))

m_etu = re.findall(r'Total étudiants inscrits public \+ privé.*?(\d{6})', full_text)
if m_etu: fields['total_students'] = int(m_etu[-1])

m_priv = re.findall(r'Pourcentage secteur privé.*?([\d,]+)%', full_text)
if m_priv: fields['private_sector_percentage'] = float(m_priv[-1].replace(',', '.'))

m_foyers = re.findall(r'Nombre de foyers universitaires.*?(\d{3})', full_text)
if m_foyers: fields['university_residences'] = int(m_foyers[-1])

m_labs = re.findall(r'Nombre de laboratoires de recherche.*?(\d{3})', full_text)
if m_labs: fields['research_labs'] = int(m_labs[-1])

print(fields)
