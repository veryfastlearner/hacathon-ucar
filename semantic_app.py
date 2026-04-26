#!/usr/bin/env python3
"""UCAR Semantic Knowledge Graph & Search Dashboard"""
import os, json, numpy as np, pandas as pd
from dotenv import load_dotenv
from supabase import create_client
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import umap, plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
from flask import Flask, render_template_string, request, jsonify

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
app = Flask(__name__)
CSV_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- Load Supabase data ----------
print("[1/5] Loading documents from Supabase...")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
resp = supabase.table("ucar_documents").select("id, content, metadata, embedding").execute()
docs = resp.data
print(f"      Loaded {len(docs)} documents")

embeddings = []
for d in docs:
    e = d["embedding"]
    embeddings.append(json.loads(e) if isinstance(e, str) else e)
X = np.array(embeddings, dtype=np.float32)
print(f"      Embedding matrix shape: {X.shape}")

# UMAP + KMeans
print("[2/5] Running UMAP...")
pos = umap.UMAP(n_neighbors=10, min_dist=0.1, n_components=2, random_state=42).fit_transform(X)
print("      UMAP done")
n_clusters = min(5, len(docs))
clusters = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(X)
print(f"[3/5] KMeans into {n_clusters} clusters done")

for i, d in enumerate(docs):
    d["x"] = float(pos[i, 0])
    d["y"] = float(pos[i, 1])
    d["cluster"] = int(clusters[i])
    d["short"] = str(d["content"])[:120].replace("\n", " ")
    d["source"] = d.get("metadata", {}).get("source", "unknown")

# ---------- Lazy model loader ----------
_encoder = None
def get_encoder():
    global _encoder
    if _encoder is None:
        print("[model] Downloading/loading all-MiniLM-L6-v2 (one-time)...")
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
        print("[model] Ready")
    return _encoder

# ---------- Build Plotly figures ----------
print("[5/5] Building Plotly visualizations...")
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]

fig_net = go.Figure()
fig_net.add_trace(go.Scatter(
    x=[d["x"] for d in docs], y=[d["y"] for d in docs],
    mode="markers+text",
    marker=dict(size=[max(8, min(30, len(d["content"])/20)) for d in docs],
                color=[colors[d["cluster"] % len(colors)] for d in docs],
                line=dict(width=1, color="#fff"), opacity=0.9),
    text=[d["source"][:15] for d in docs], textposition="top center",
    textfont=dict(size=8, color="#ccc"),
    hovertext=[f"<b>Source:</b> {d['source']}<br><b>Cluster:</b> {d['cluster']}<br><b>Page:</b> {d.get('metadata',{}).get('page','?')}<br><br>{d['short']}..." for d in docs],
    hoverinfo="text",
))
fig_net.update_layout(
    title=dict(text="Semantic Knowledge Graph — Document Embeddings (UMAP)", font=dict(color="#fff", size=18), x=0.5),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="#cbd5e1"),
    margin=dict(l=20, r=20, t=60, b=20), height=650, dragmode="pan", hovermode="closest",
)

def load_csv(name):
    try:
        return pd.read_csv(os.path.join(CSV_DIR, f"{name}.csv"))
    except Exception:
        return None

ss = load_csv("the_ucar_rankings_student_stats")
ps = load_csv("the_ucar_rankings_wur_pillar_scores")
ir = load_csv("the_ucar_rankings_impact_rankings")

if ss is not None:
    ss = ss.sort_values("year")
    fig_students = go.Figure()
    fig_students.add_trace(go.Scatter(x=ss["year"], y=ss["total_students"], mode="lines+markers", name="Total Students", line=dict(color="#38bdf8", width=3)))
    fig_students.add_trace(go.Scatter(x=ss["year"], y=ss["students_per_staff"], mode="lines+markers", name="Students/Staff", line=dict(color="#f472b6", width=2, dash="dash"), yaxis="y2"))
    fig_students.update_layout(yaxis2=dict(overlaying="y", side="right"), plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="#cbd5e1"), legend=dict(orientation="h", yanchor="bottom", y=-0.2), margin=dict(l=40, r=40, t=40, b=40), height=350, title="Student Enrollment Trend")
else:
    fig_students = go.Figure()

if ps is not None:
    latest = ps[ps["year"] == ps["year"].max()]
    overall = latest[latest["subject"] == "Overall"]
    pillars = {row["pillar"]: float(row["score"]) for _, row in overall.iterrows()}
    fig_pillars = go.Figure(go.Bar(x=list(pillars.keys()), y=list(pillars.values()), marker_color=["#38bdf8", "#f472b6", "#34d399", "#fbbf24", "#a78bfa"], text=[f"{v:.1f}" for v in pillars.values()], textposition="outside"))
    fig_pillars.update_layout(yaxis=dict(range=[0, 60]), plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="#cbd5e1"), margin=dict(l=40, r=40, t=40, b=40), height=350, title="2026 Overall Pillar Scores")
else:
    fig_pillars = go.Figure()

if ir is not None:
    latest_ir = ir[ir["year"] == ir["year"].max()]
    rows = [row for _, row in latest_ir.iterrows() if pd.notna(row.get("score_lower"))]
    sdgs = [row["sdg"][:20] for row in rows]
    mids = [(float(row["score_lower"]) + float(row["score_higher"])) / 2 for row in rows]
    errs = [float(row["score_higher"]) - m for row, m in zip(rows, mids)]
    fig_impact = go.Figure(go.Bar(x=sdgs, y=mids, error_y=dict(type="data", symmetric=False, array=errs, arrayminus=errs), marker_color="#e879f9"))
    fig_impact.update_layout(plot_bgcolor="#0f172a", paper_bgcolor="#0f172a", font=dict(color="#cbd5e1"), margin=dict(l=40, r=40, t=40, b=80), height=350, xaxis_tickangle=-45, title="Impact Rankings SDG Scores")
else:
    fig_impact = go.Figure()

net_json = json.dumps(fig_net, cls=PlotlyJSONEncoder)
stud_json = json.dumps(fig_students, cls=PlotlyJSONEncoder)
pill_json = json.dumps(fig_pillars, cls=PlotlyJSONEncoder)
imp_json = json.dumps(fig_impact, cls=PlotlyJSONEncoder)

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, net_json=net_json, stud_json=stud_json, pill_json=pill_json, imp_json=imp_json)

@app.route("/api/search", methods=["POST"])
def search():
    query = request.json.get("query", "")
    if not query:
        return jsonify([])
    q_emb = get_encoder().encode(query).tolist()
    q_emb_str = json.dumps(q_emb)
    resp = supabase.rpc("match_ucar_docs", {"query_embedding": q_emb_str, "match_threshold": 0.1, "match_count": 5}).execute()
    results = []
    for r in (resp.data or []):
        results.append({
            "source": r.get("metadata", {}).get("source", "unknown"),
            "page": r.get("metadata", {}).get("page", "?"),
            "content": str(r.get("content", ""))[:500],
        })
    return jsonify(results)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UCAR Semantic Knowledge Graph</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  body { background-color: #0b1120; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; }
  .glass { background: rgba(30,41,59,0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.08); border-radius: 1rem; }
  .card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.4); }
  .transition-all { transition: all 0.3s ease; }
  input { background: #1e293b; border: 1px solid #334155; color: #e2e8f0; }
  input:focus { outline: none; border-color: #38bdf8; }
  ::-webkit-scrollbar { width: 8px; }
  ::-webkit-scrollbar-track { background: #0b1120; }
  ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
</style>
</head>
<body class="min-h-screen">
<header class="py-6 px-8 border-b border-slate-800">
  <div class="max-w-7xl mx-auto flex items-center justify-between">
    <div>
      <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-sky-400 to-purple-400">University of Carthage</h1>
      <p class="text-slate-400 text-sm mt-1">Semantic Knowledge Graph · Embeddings · KPI Dashboard</p>
    </div>
    <div class="text-xs text-slate-500 text-right">
      <div>Documents: 74</div>
      <div>Model: all-MiniLM-L6-v2</div>
    </div>
  </div>
</header>

<main class="max-w-7xl mx-auto p-6 space-y-8">
  <!-- Semantic Graph -->
  <section class="glass p-4 card-hover transition-all">
    <h2 class="text-xl font-semibold mb-3 text-sky-300">Semantic Document Graph (UMAP + KMeans)</h2>
    <div id="graph-net" style="width:100%;height:650px;"></div>
  </section>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Search -->
    <section class="glass p-5 card-hover transition-all lg:col-span-1">
      <h2 class="text-lg font-semibold mb-3 text-purple-300">Semantic Search</h2>
      <div class="flex gap-2 mb-4">
        <input id="searchInput" type="text" placeholder="Ask about UCAR..." class="w-full px-3 py-2 rounded-lg text-sm">
        <button onclick="doSearch()" class="px-4 py-2 bg-sky-600 hover:bg-sky-500 rounded-lg text-sm font-semibold transition-colors">Search</button>
      </div>
      <div id="searchResults" class="space-y-3 max-h-[420px] overflow-y-auto pr-1"></div>
    </section>

    <!-- KPI Charts -->
    <section class="glass p-4 card-hover transition-all lg:col-span-2">
      <h2 class="text-lg font-semibold mb-3 text-emerald-300">Key Performance Indicators</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div id="graph-stud" style="width:100%;height:320px;"></div>
        <div id="graph-pill" style="width:100%;height:320px;"></div>
        <div id="graph-imp" style="width:100%;height:320px;" class="md:col-span-2"></div>
      </div>
    </section>
  </div>
</main>

<footer class="py-6 text-center text-xs text-slate-600 border-t border-slate-800 mt-8">
  Powered by Supabase + UMAP + Plotly + Flask
</footer>

<script>
  var netData = {{ net_json | safe }};
  var studData = {{ stud_json | safe }};
  var pillData = {{ pill_json | safe }};
  var impData = {{ imp_json | safe }};
  Plotly.newPlot('graph-net', netData.data, netData.layout, {responsive:true});
  Plotly.newPlot('graph-stud', studData.data, studData.layout, {responsive:true});
  Plotly.newPlot('graph-pill', pillData.data, pillData.layout, {responsive:true});
  Plotly.newPlot('graph-imp', impData.data, impData.layout, {responsive:true});

  async function doSearch() {
    const q = document.getElementById('searchInput').value.trim();
    if (!q) return;
    const resDiv = document.getElementById('searchResults');
    resDiv.innerHTML = '<div class="text-slate-400 text-sm">Searching...</div>';
    try {
      const resp = await fetch('/api/search', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({query: q}) });
      const data = await resp.json();
      if (!data.length) { resDiv.innerHTML = '<div class="text-slate-400 text-sm">No results.</div>'; return; }
      resDiv.innerHTML = data.map((r,i) => `
        <div class="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50 hover:border-sky-500/50 transition-colors">
          <div class="flex justify-between text-xs text-slate-400 mb-1">
            <span>${r.source}</span><span>page ${r.page}</span>
          </div>
          <p class="text-sm text-slate-200 leading-relaxed">${r.content}</p>
        </div>
      `).join('');
    } catch(e) {
      resDiv.innerHTML = '<div class="text-red-400 text-sm">Error: ' + e.message + '</div>';
    }
  }
  document.getElementById('searchInput').addEventListener('keypress', e => { if (e.key === 'Enter') doSearch(); });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("\n>>> Starting server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
