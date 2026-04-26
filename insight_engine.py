#!/usr/bin/env python3
"""UCAR Insight Engine — Fact-Based Knowledge Graph"""
import os, json, re, math, time, hashlib
from collections import defaultdict, Counter
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder
from flask import Flask, render_template_string
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_KEY = os.getenv("gemini_api_key")
app = Flask(__name__)
CSV_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(CSV_DIR, "all_docs.json"), "r", encoding="utf-8") as f:
    DOCS = json.load(f)
print(f"[1/6] Loaded {len(DOCS)} documents")

def smart_extract(text_chunk):
    """
    Instead of Regex, we use Gemini to turn raw text into structured JSON.
    """
    client = genai.Client(api_key=GEMINI_KEY)
    
    prompt = f"""
    Analyze the following educational data:
    "{text_chunk}"
    
    Extract:
    1. Metrics (Value, Unit, Type - e.g., dropout, cost, ratio)
    2. Entities (Institutions, Locations, Certifications)
    3. Links (How do these relate? e.g., "FSB is in Bizerte")
    
    Return ONLY valid JSON in this format:
    {{
      "metrics": [{"type": "dropout", "value": 66, "unit": "%"}],
      "entities": [{"type": "institution", "name": "FSB"}],
      "links": [{"source": "FSB", "target": "dropout", "relationship": "reports"}]
    }}
    """
    
    response = client.models.generate_content(
        model="gemini-3-flash",
        contents=prompt,
        config={'response_mime_type': 'application/json'}
    )
    return json.loads(response.text)

class FactExtractor:
    def __init__(self):
        self.facts = []
        self.entities = []
    def extract(self, docs):
        for doc in docs:
            did, content = doc["id"], str(doc.get("content", ""))
            meta = doc.get("metadata", {})
            src, page = meta.get("source", "unknown"), meta.get("page", "?")
            for pat, cat, etype, unit in METRIC_PATTERNS:
                for m in re.finditer(pat, content, re.IGNORECASE):
                    vs = m.group(1).replace(" ", "").replace(",", ".")
                    try:
                        v = float(vs)
                    except ValueError:
                        continue
                    self.facts.append({"type":"metric","category":cat,"entity_type":etype,"value":v,"unit":unit,
                        "text":content[max(0,m.start()-40):m.end()+40].replace("\n"," "),
                        "doc_id":did,"source":src,"page":page,"confidence":0.85})
            for pat, etype in ENTITY_PATTERNS:
                for m in re.finditer(pat, content):
                    name = m.group(0).strip()
                    if len(name) > 2:
                        self.entities.append({"type":"entity","entity_type":etype,"name":name,"doc_id":did,"source":src,"page":page})
            for m in re.finditer(r"(High|Critical|Moderate|Low|Stable|Optimal|Challenged)\b", content):
                label = m.group(1)
                ctx = content[max(0,m.start()-60):m.end()+60]
                self.facts.append({"type":"assessment","category":"risk","entity_type":"risk_label","value":label,"unit":"label",
                    "text":ctx.replace("\n"," "),"doc_id":did,"source":src,"page":page,"confidence":0.7})
        print(f"[2/6] Extracted {len(self.facts)} facts and {len(self.entities)} entities")
        return self.facts, self.entities

extractor = FactExtractor()
FACTS, ENTITIES = extractor.extract(DOCS)

class FactGraph:
    def __init__(self, facts, entities):
        self.nodes = {}
        self.edges = []
        self.facts = facts
        self.entities = entities
        self._build()
    def _nid(self, item):
        if item["type"] == "metric":
            return f"M_{item['entity_type']}_{item['doc_id'][:8]}_{hash(item['text'])%10000}"
        elif item["type"] == "assessment":
            return f"A_{item['value']}_{item['doc_id'][:8]}"
        return f"E_{item['entity_type']}_{item['name'][:30].replace(' ','_')}"
    def _build(self):
        for f in self.facts:
            nid = self._nid(f)
            size = 20 if f["entity_type"] in ("dropout_rate","success_rate","cost_per_student") else 12
            color = {"academic":"#ef4444","enrollment":"#3b82f6","finance":"#f59e0b","hr":"#8b5cf6",
                     "demographics":"#ec4899","research":"#10b981","ranking":"#6366f1",
                     "certification":"#14b8a6","partnership":"#f97316","risk":"#dc2626"}.get(f["category"], "#94a3b8")
            self.nodes[nid] = {"id":nid,"label":f"{f['entity_type']}: {f['value']}{f['unit']}" if f["type"]=="metric" else f"{f['value']}",
                "type":f["type"],"category":f["category"],"entity_type":f["entity_type"],
                "value":f["value"],"unit":f["unit"],"snippet":f["text"][:100],
                "source":f["source"],"page":f["page"],"size":size,"color":color}
        for e in self.entities:
            nid = self._nid(e)
            if nid not in self.nodes:
                self.nodes[nid] = {"id":nid,"label":e["name"][:40],"type":"entity","entity_type":e["entity_type"],"category":e["entity_type"],
                    "source":e["source"],"page":e["page"],"size":14,"color":"#64748b"}
        # co-occurrence edges
        doc_facts = defaultdict(list)
        for f in self.facts:
            doc_facts[f["doc_id"]].append(self._nid(f))
        for did, nids in doc_facts.items():
            for i in range(len(nids)):
                for j in range(i+1, len(nids)):
                    self.edges.append((nids[i], nids[j], "co-occurs", 0.5))
        # category edges
        cat_nodes = defaultdict(list)
        for nid, n in self.nodes.items():
            if n["type"] in ("metric","assessment"):
                cat_nodes[n["category"]].append(nid)
        for cat, nids in cat_nodes.items():
            for i in range(len(nids)):
                for j in range(i+1, len(nids)):
                    self.edges.append((nids[i], nids[j], "same_category", 0.3))
        # entity->fact edges
        edmap = defaultdict(set)
        for e in self.entities:
            edmap[e["doc_id"]].add(self._nid(e))
        for f in self.facts:
            for eid in edmap.get(f["doc_id"], []):
                self.edges.append((self._nid(f), eid, "mentions", 0.4))
        # anomaly edges
        for nid, n in self.nodes.items():
            if n["type"]=="metric" and n["entity_type"]=="dropout_rate" and isinstance(n["value"],(int,float)) and n["value"]>50:
                for nid2, n2 in self.nodes.items():
                    if n2["type"]=="metric" and n2["entity_type"]=="success_rate" and isinstance(n2["value"],(int,float)):
                        self.edges.append((nid, nid2, "anomaly_contrast", 0.9))
        # cost-student edges
        for c in [nid for nid,n in self.nodes.items() if n["entity_type"]=="cost_per_student"]:
            for s in [nid for nid,n in self.nodes.items() if n["entity_type"]=="student_count"]:
                self.edges.append((c, s, "cost_vs_students", 0.6))
        print(f"[3/6] Graph: {len(self.nodes)} nodes, {len(self.edges)} edges")
    def layout(self):
        pos = {}
        cats = defaultdict(list)
        for nid, n in self.nodes.items():
            cats[n["category"]].append(nid)
        angle = 0
        for cat, nids in cats.items():
            step = 2*math.pi/max(len(nids),1)
            for i, nid in enumerate(nids):
                r = 3 + (i%3)*1.5
                pos[nid] = (r*math.cos(angle+i*step), r*math.sin(angle+i*step))
            angle += 2*math.pi/max(len(cats),1)
        return pos

graph = FactGraph(FACTS, ENTITIES)

class InsightEngine:
    def __init__(self, facts):
        self.facts = facts
        self.anomalies = []
        self.insights = []
        self._detect()
    def _detect(self):
        by_type = defaultdict(list)
        for f in self.facts:
            if f["type"]=="metric" and isinstance(f["value"],(int,float)):
                by_type[f["entity_type"]].append(f)
        for etype, items in by_type.items():
            if len(items) < 2: continue
            vals = np.array([i["value"] for i in items])
            mean, std = np.mean(vals), np.std(vals) or 1e-6
            zs = np.abs((vals-mean)/std)
            for i, z in enumerate(zs):
                if z > 1.5 or (etype=="dropout_rate" and items[i]["value"]>50):
                    self.anomalies.append({"fact":items[i],"z_score":float(z),"severity":"high" if z>2 or items[i]["value"]>60 else "medium",
                        "reason":f"{etype} = {items[i]['value']}{items[i]['unit']} is {z:.1f}σ from mean ({mean:.1f})"})
        for f in self.facts:
            if f["entity_type"]=="dropout_rate" and f["value"]>60:
                self.anomalies.append({"fact":f,"z_score":99,"severity":"critical","reason":f"CRITICAL: PhD dropout {f['value']}% indicates systemic crisis"})
            if f["entity_type"]=="cost_per_student" and f["value"]>7000:
                self.anomalies.append({"fact":f,"z_score":99,"severity":"high","reason":f"Cost per student ({f['value']} TND) exceeds peer benchmarks"})
            if f["entity_type"]=="international_pct" and f["value"]<2:
                self.anomalies.append({"fact":f,"z_score":99,"severity":"medium","reason":f"International ratio ({f['value']}%) is very low — limits global ranking growth"})
        drop = [f for f in self.facts if f["entity_type"]=="dropout_rate"]
        cost = [f for f in self.facts if f["entity_type"]=="cost_per_student"]
        if drop and cost:
            self.insights.append({"type":"correlation","title":"Cost-Dropout Hypothesis",
                "text":f"High cost ({cost[0]['value']} TND) coincides with {drop[0]['value']}% PhD dropout. Potential causality: financial burden → attrition."})
        rank = [f for f in self.facts if f["entity_type"]=="national_rank"]
        if rank:
            self.insights.append({"type":"ranking","title":"National Standing",
                "text":f"UCAR maintains rank #{int(rank[0]['value'])} nationally — stable but room for improvement via research output and internationalization."})
        print(f"[4/6] {len(self.anomalies)} anomalies, {len(self.insights)} insights")

engine = InsightEngine(FACTS)

GEMINI_CACHE_FILE = os.path.join(CSV_DIR, "gemini_cache.json")
gemini_cache = {}
if os.path.exists(GEMINI_CACHE_FILE):
    with open(GEMINI_CACHE_FILE, "r", encoding="utf-8") as f:
        gemini_cache = json.load(f)
_gemini_ok = False
if GEMINI_KEY:
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_KEY)
        _gemini_ok = True
        print("[5/6] Gemini configured")
    except Exception as e:
        print(f"[5/6] Gemini init failed: {e}")

def gemini_synthesize(prompt, max_retries=3):
    if not _gemini_ok or not GEMINI_KEY:
        return "[Gemini unavailable — local analysis only]"
    ck = hashlib.md5(prompt.encode()).hexdigest()
    if ck in gemini_cache:
        return gemini_cache[ck]
    for attempt in range(max_retries):
        try:
            time.sleep(2**attempt)
            resp = _gemini_client.models.generate_content(model="gemini-3-flash-preview", contents=prompt, config={"max_output_tokens":512, "temperature":0.3})
            text = resp.text
            gemini_cache[ck] = text
            with open(GEMINI_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(gemini_cache, f, ensure_ascii=False)
            return text
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                print(f"  Gemini quota, retry in {2**(attempt+1)}s...")
                continue
            return f"[Gemini error: {e}]"
    return "[Gemini rate limited — local insights only]"

_key_syntheses = {}
if FACTS:
    anom_sum = "\n".join([a["reason"] for a in engine.anomalies[:5]])
    prompt = f"""You are an education policy analyst. Given these anomalies from University of Carthage data:
{anom_sum}

Provide 3 concise actionable recommendations. Format as bullet points."""
    _key_syntheses["recs"] = gemini_synthesize(prompt)
    prompt2 = f"""Given: dropout rate 66%, national success rate 74.1%, cost per student 7705 TND, student/teacher ratio 11.3, rank #2 nationally.

Identify the single most important causal chain and suggest one intervention point. Be concise."""
    _key_syntheses["causal"] = gemini_synthesize(prompt2)
    print(f"[5/6] Synthesis done")

print("[6/6] Building visualizations...")
pos = graph.layout()
edge_x, edge_y = [], []
for s, t, l, w in graph.edges:
    if s in pos and t in pos:
        edge_x += [pos[s][0], pos[t][0], None]
        edge_y += [pos[s][1], pos[t][1], None]

node_x, node_y, node_color, node_size, node_text, node_hover = [], [], [], [], [], []
for nid, n in graph.nodes.items():
    if nid in pos:
        node_x.append(pos[nid][0]); node_y.append(pos[nid][1])
        node_color.append(n["color"]); node_size.append(n["size"])
        node_text.append(n["label"][:25])
        node_hover.append(f"<b>{n['label']}</b><br>Category: {n['category']}<br>Type: {n['entity_type']}<br>Source: {n['source']} p.{n['page']}<br><br>{n.get('snippet','')}")

fig_net = go.Figure()
fig_net.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(color='#334155', width=0.5), hoverinfo='none', showlegend=False))
fig_net.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text',
    marker=dict(color=node_color, size=node_size, line=dict(width=1, color='#0f172a')),
    text=node_text, textposition="top center", textfont=dict(size=8, color='#94a3b8'),
    hovertext=node_hover, hoverinfo='text', showlegend=False))
fig_net.update_layout(
    title=dict(text="Fact-Based Knowledge Graph — Metrics, Entities & Relationships", font=dict(color="#e2e8f0", size=16), x=0.5),
    plot_bgcolor="#0b1120", paper_bgcolor="#0b1120", font=dict(color="#94a3b8"),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    margin=dict(l=20,r=20,t=60,b=20), height=700, dragmode='pan', hovermode='closest')

fig_anom = make_subplots(rows=2, cols=2, subplot_titles=("Severity","Value Distribution","Anomaly Timeline","Insights"),
    specs=[[{"type":"bar"},{"type":"histogram"}],[{"type":"scatter"},{"type":"table"}]])
if engine.anomalies:
    sev_counts = Counter(a["severity"] for a in engine.anomalies)
    fig_anom.add_trace(go.Bar(x=list(sev_counts.keys()), y=list(sev_counts.values()), marker_color=["#dc2626","#f59e0b","#3b82f6"], name="Severity"), row=1, col=1)
    vals = [a["fact"]["value"] for a in engine.anomalies if isinstance(a["fact"]["value"],(int,float))]
    fig_anom.add_trace(go.Histogram(x=vals, nbinsx=10, marker_color="#8b5cf6", name="Values"), row=1, col=2)
    atexts = [a["reason"][:55]+"..." for a in engine.anomalies[:10]]
    ascores = [a["z_score"] for a in engine.anomalies[:10]]
    fig_anom.add_trace(go.Scatter(x=list(range(len(ascores))), y=ascores, mode='markers+text',
        text=atexts, textposition='top center', marker=dict(size=12, color="#ef4444"), name="Anomalies"), row=2, col=1)
    itexts = [[i["title"], i["text"][:110]] for i in engine.insights[:6]]
    fig_anom.add_trace(go.Table(
        header=dict(values=["Insight","Description"], fill_color="#1e293b", line_color="#334155", font=dict(color="#e2e8f0")),
        cells=dict(values=[[r[0] for r in itexts], [r[1] for r in itexts]], fill_color="#0f172a", line_color="#334155", font=dict(color="#94a3b8"))),
        row=2, col=2)
fig_anom.update_layout(title=dict(text="Anomaly Detection & Insight Engine", font=dict(color="#e2e8f0"), x=0.5),
    plot_bgcolor="#0b1120", paper_bgcolor="#0b1120", font=dict(color="#94a3b8"), height=900, margin=dict(l=40,r=40,t=60,b=40), showlegend=False)

fig_tree = go.Figure(go.Treemap(labels=[f"{k} ({v})" for k,v in Counter(f["category"] for f in FACTS).items()],
    parents=[""]*len(Counter(f["category"] for f in FACTS)), values=list(Counter(f["category"] for f in FACTS).values()),
    textinfo="label", marker=dict(colors=["#3b82f6","#ef4444","#f59e0b","#8b5cf6","#ec4899","#10b981","#6366f1","#14b8a6"])))
fig_tree.update_layout(title=dict(text="Fact Categories", font=dict(color="#e2e8f0"), x=0.5), paper_bgcolor="#0b1120", font=dict(color="#e2e8f0"), margin=dict(t=40,b=20,l=20,r=20), height=400)

net_json = json.dumps(fig_net, cls=PlotlyJSONEncoder)
anom_json = json.dumps(fig_anom, cls=PlotlyJSONEncoder)
tree_json = json.dumps(fig_tree, cls=PlotlyJSONEncoder)

@app.route("/")
def index():
    return render_template_string(HTML,
        net_json=net_json, anom_json=anom_json, tree_json=tree_json,
        nodes=len(graph.nodes), edges=len(graph.edges), anomalies=len(engine.anomalies),
        recs=_key_syntheses.get("recs","[Gemini unavailable — local analysis only]"),
        causal=_key_syntheses.get("causal","[Gemini unavailable — local analysis only]"))

HTML = open(os.path.join(CSV_DIR, "insight_template.html"), "r", encoding="utf-8").read()

if __name__ == "__main__":
    print("\n>>> Starting server on http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
