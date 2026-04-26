import json

def find_key(obj, key, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(v).find(key) != -1:
                print(f"Found '{key}' in {path}/{k}")
            find_key(v, key, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if str(v).find(key) != -1:
                print(f"Found '{key}' in {path}[{i}]")
            find_key(v, key, path + f"[{i}]")

d = json.load(open('data.json', encoding='utf-8'))
find_key(d['props']['pageProps'], 'Engineering')
find_key(d['props']['pageProps'], 'Life Sciences')
