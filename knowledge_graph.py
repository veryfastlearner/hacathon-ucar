#!/usr/bin/env python3
"""
UCAR Knowledge Graph & KPI Dashboard
--------------------------------------
Builds an interactive knowledge graph from all scraped CSV datasets
and generates Plotly visualizations with KPI insights.

Outputs:
    - knowledge_graph.html    : Interactive network graph
    - kpi_dashboard.html      : KPI charts and dashboards
"""

import os
import glob
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import defaultdict, Counter

# ---------------------------------------------------------------------------
# 1. LOAD ALL CSV FILES
# ---------------------------------------------------------------------------
CSV_DIR = os.path.dirname(os.path.abspath(__file__))

def load_all_csvs():
    """Discover and load every CSV in the project folder."""
    files = glob.glob(os.path.join(CSV_DIR, "*.csv"))
    data = {}
    for f in sorted(files):
        name = os.path.splitext(os.path.basename(f))[0]
        try:
            df = pd.read_csv(f)
            data[name] = df
            print(f"[OK] {name}: {len(df)} rows x {len(df.columns)} cols")
        except Exception as e:
            print(f"[ERR] {name}: {e}")
    return data

# ---------------------------------------------------------------------------
# 2. KNOWLEDGE GRAPH CONSTRUCTION
# ---------------------------------------------------------------------------
class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}   # id -> {label, type, size, color, meta}
        self.edges = []   # [(source, target, label, weight)]

    def add_node(self, node_id, label, node_type, size=10, color=None, meta=None):
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "label": label,
                "type": node_type,
                "size": size,
                "color": color or self._type_color(node_type),
                "meta": meta or {},
            }
        return node_id

    def add_edge(self, source, target, label="", weight=1):
        self.edges.append((source, target, label, weight))

    @staticmethod
    def _type_color(node_type):
        palette = {
            "university": "#1f77b4",
            "data_source": "#ff7f0e",
            "dataset": "#2ca02c",
            "year": "#d62728",
            "subject": "#9467bd",
            "pillar": "#8c564b",
            "sdg": "#e377c2",
            "rank": "#7f7f7f",
            "kpi": "#bcbd22",
            "research": "#17becf",
            "lab": "#aec7e8",
            "person": "#ffbb78",
        }
        return palette.get(node_type, "#333")

    def build_from_data(self, data):
        """Construct the graph from all loaded dataframes."""
        # Central node
        self.add_node("UCAR", "University of Carthage", "university", size=40, color="#1f77b4")

        # Data source nodes
        self.add_node("THE", "Times Higher Education", "data_source", size=25, color="#ff7f0e")
        self.add_node("UCAR_WEB", "UCAR Official Website", "data_source", size=25, color="#ff7f0e")
        self.add_edge("UCAR", "THE", "ranked_by")
        self.add_edge("UCAR", "UCAR_WEB", "described_by")

        # --- THE HEADER INFO ---
        if "the_ucar_rankings_header_info" in data:
            hi = data["the_ucar_rankings_header_info"]
            self.add_node("DS_HEADER", "Header Info", "dataset", size=15, color="#2ca02c")
            self.add_edge("THE", "DS_HEADER", "dataset")
            self.add_edge("UCAR", "DS_HEADER", "has")
            for _, row in hi.iterrows():
                rank = str(row.get("wur_rank", ""))
                rank_y = str(row.get("wur_rank_year", ""))
                self.add_node(f"RANK_{rank_y}", f"WUR {rank_y}: {rank}", "rank", size=18, color="#d62728")
                self.add_edge("UCAR", f"RANK_{rank_y}", f"ranked")

        # --- STUDENT STATS ---
        if "the_ucar_rankings_student_stats" in data:
            ss = data["the_ucar_rankings_student_stats"]
            self.add_node("DS_STUDENTS", "Student Statistics", "dataset", size=15, color="#2ca02c")
            self.add_edge("THE", "DS_STUDENTS", "dataset")
            self.add_edge("UCAR", "DS_STUDENTS", "has")
            for _, row in ss.iterrows():
                year = int(row["year"])
                y_node = self.add_node(f"YEAR_{year}", str(year), "year", size=12)
                self.add_edge("DS_STUDENTS", y_node, "year")
                self.add_edge("UCAR", y_node, "year")
                # KPI nodes
                total = row.get("total_students")
                if pd.notna(total):
                    kpi_id = f"STUDENTS_{year}"
                    self.add_node(kpi_id, f"{int(total):,} students", "kpi", size=8, color="#bcbd22")
                    self.add_edge(y_node, kpi_id, "students")

        # --- WUR PILLAR SCORES ---
        if "the_ucar_rankings_wur_pillar_scores" in data:
            ps = data["the_ucar_rankings_wur_pillar_scores"]
            self.add_node("DS_PILLARS", "WUR Pillar Scores", "dataset", size=15, color="#2ca02c")
            self.add_edge("THE", "DS_PILLARS", "dataset")
            self.add_edge("UCAR", "DS_PILLARS", "has")
            subjects = ps["subject"].unique()
            for subj in subjects:
                subj_id = f"SUBJ_{subj.replace(' ', '_').replace('&', 'and')}"
                self.add_node(subj_id, subj, "subject", size=14)
                self.add_edge("DS_PILLARS", subj_id, "subject")
                self.add_edge("UCAR", subj_id, "offers")
            pillars = ps["pillar"].unique()
            for pillar in pillars:
                p_id = f"PILLAR_{pillar.replace(' ', '_')}"
                self.add_node(p_id, pillar, "pillar", size=11, color="#8c564b")
                self.add_edge("DS_PILLARS", p_id, "measured_by")

        # --- SUBJECT RANKINGS ---
        if "the_ucar_rankings_subject_rankings" in data:
            sr = data["the_ucar_rankings_subject_rankings"]
            self.add_node("DS_SUBJ_RANK", "Subject Rankings", "dataset", size=15, color="#2ca02c")
            self.add_edge("THE", "DS_SUBJ_RANK", "dataset")
            for _, row in sr.iterrows():
                subj = row.get("subject", "")
                rank = str(row.get("rank_display", ""))
                subj_id = f"SUBJ_{subj.replace(' ', '_').replace('&', 'and')}"
                self.add_node(f"SRANK_{subj_id}", f"{subj}: {rank}", "rank", size=10, color="#7f7f7f")
                self.add_edge("DS_SUBJ_RANK", f"SRANK_{subj_id}", "rank")

        # --- IMPACT RANKINGS (SDGs) ---
        if "the_ucar_rankings_impact_rankings" in data:
            ir = data["the_ucar_rankings_impact_rankings"]
            self.add_node("DS_IMPACT", "Impact Rankings (SDGs)", "dataset", size=15, color="#2ca02c")
            self.add_edge("THE", "DS_IMPACT", "dataset")
            self.add_edge("UCAR", "DS_IMPACT", "measured_by")
            sdgs = ir["sdg"].unique()
            for sdg in sdgs:
                s_id = f"SDG_{sdg.replace(' ', '_').replace(',', '')}"
                self.add_node(s_id, sdg, "sdg", size=10, color="#e377c2")
                self.add_edge("DS_IMPACT", s_id, "sdg")
                self.add_edge("UCAR", s_id, "contributes_to")

        # --- SUBJECTS TAUGHT ---
        if "the_ucar_rankings_subjects_taught" in data:
            st = data["the_ucar_rankings_subjects_taught"]
            self.add_node("DS_SUBJ_TAUGHT", "Subjects Taught", "dataset", size=15, color="#2ca02c")
            self.add_edge("THE", "DS_SUBJ_TAUGHT", "dataset")
            n_subjects = len(st)
            kpi_id = "KPI_SUBJECTS"
            self.add_node(kpi_id, f"{n_subjects} subjects", "kpi", size=16, color="#bcbd22")
            self.add_edge("UCAR", kpi_id, "offers")
            self.add_edge("DS_SUBJ_TAUGHT", kpi_id, "count")

        # --- UCAR WEBSITE DATA ---
        for key in data:
            if key.startswith("ucar_data_"):
                cat = key.replace("ucar_data_", "").upper()
                self.add_node(f"UCAR_{cat}", cat, "dataset", size=12, color="#2ca02c")
                self.add_edge("UCAR_WEB", f"UCAR_{cat}", "dataset")
                self.add_edge("UCAR", f"UCAR_{cat}", "has")
                df = data[key]
                n = len(df)
                kpi_id = f"KPI_UCAR_{cat}"
                self.add_node(kpi_id, f"{n} records", "kpi", size=8, color="#bcbd22")
                self.add_edge(f"UCAR_{cat}", kpi_id, "count")

        # --- RESEARCH LABS ---
        if "ucar_data_research" in data:
            labs = data["ucar_data_research"]
            lab_names = labs["Name"].dropna().unique() if "Name" in labs.columns else []
            for lab in lab_names[:30]:  # cap for readability
                lab_id = f"LAB_{lab.replace(' ', '_')[:40]}"
                self.add_node(lab_id, lab[:40], "lab", size=8, color="#aec7e8")
                self.add_edge("UCAR_RESEARCH", lab_id, "contains")

        print(f"\nGraph built: {len(self.nodes)} nodes, {len(self.edges)} edges")

    def compute_layout(self):
        """Simple force-directed layout for the network graph."""
        import random
        random.seed(42)
        positions = {}
        # Place central node at origin
        positions["UCAR"] = (0, 0)
        # Data sources around center
        positions["THE"] = (-3, 2)
        positions["UCAR_WEB"] = (3, 2)
        # Dataset nodes further out
        ds_nodes = [n for n, info in self.nodes.items() if info["type"] == "dataset"]
        angle_step = 2 * np.pi / max(len(ds_nodes), 1)
        for i, n in enumerate(ds_nodes):
            r = 5 + random.uniform(-0.5, 0.5)
            positions[n] = (r * np.cos(i * angle_step), r * np.sin(i * angle_step))
        # Everything else: simple spring-like placement
        for n in self.nodes:
            if n in positions:
                continue
            # Find connected nodes
            neighbors = [e[1] if e[0] == n else e[0] for e in self.edges if n in (e[0], e[1])]
            if neighbors:
                valid = [positions[k] for k in neighbors if k in positions]
                if valid:
                    cx = np.mean([p[0] for p in valid])
                    cy = np.mean([p[1] for p in valid])
                    positions[n] = (cx + random.uniform(-1.5, 1.5), cy + random.uniform(-1.5, 1.5))
                else:
                    positions[n] = (random.uniform(-8, 8), random.uniform(-8, 8))
            else:
                positions[n] = (random.uniform(-8, 8), random.uniform(-8, 8))
        return positions

    def to_plotly_network(self):
        """Return Plotly figure for the knowledge graph network."""
        pos = self.compute_layout()
        edge_x, edge_y = [], []
        edge_text = []
        for s, t, lbl, w in self.edges:
            if s in pos and t in pos:
                edge_x += [pos[s][0], pos[t][0], None]
                edge_y += [pos[s][1], pos[t][1], None]
                edge_text.append(lbl)

        node_x, node_y, node_color, node_size, node_text, node_hover = [], [], [], [], [], []
        for nid, info in self.nodes.items():
            if nid in pos:
                node_x.append(pos[nid][0])
                node_y.append(pos[nid][1])
                node_color.append(info["color"])
                node_size.append(info["size"])
                node_text.append(info["label"])
                meta = info.get("meta", {})
                hover = f"<b>{info['label']}</b><br>Type: {info['type']}"
                if meta:
                    hover += "<br>" + "<br>".join(f"{k}: {v}" for k, v in list(meta.items())[:5])
                node_hover.append(hover)

        fig = go.Figure()
        # Edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            mode='lines',
            line=dict(color='#888', width=1),
            hoverinfo='none',
            showlegend=False
        ))
        # Nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(color=node_color, size=node_size, line=dict(width=1, color='#333')),
            text=node_text,
            textposition="top center",
            textfont=dict(size=9, color='#222'),
            hovertext=node_hover,
            hoverinfo='text',
            showlegend=False
        ))
        fig.update_layout(
            title=dict(text="UCAR Knowledge Graph — All Datasets & Relationships", x=0.5),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=20, r=20, t=60, b=20),
            height=800,
            width=1200,
            hovermode='closest',
            dragmode='pan'
        )
        return fig

# ---------------------------------------------------------------------------
# 3. KPI COMPUTATION
# ---------------------------------------------------------------------------
def compute_kpis(data):
    kpis = {}

    # --- Student growth ---
    if "the_ucar_rankings_student_stats" in data:
        ss = data["the_ucar_rankings_student_stats"]
        ss = ss.sort_values("year")
        kpis["student_growth"] = {
            "years": ss["year"].tolist(),
            "total_students": ss["total_students"].tolist(),
            "female_pct": ss["female_student_pct"].tolist(),
            "intl_pct": [v * 100 for v in ss["international_student_pct"].tolist()],
            "staff_ratio": ss["students_per_staff"].tolist(),
        }
        kpis["latest_students"] = int(ss.iloc[-1]["total_students"])
        kpis["latest_female_pct"] = float(ss.iloc[-1]["female_student_pct"])
        kpis["latest_intl_pct"] = float(ss.iloc[-1]["international_student_pct"]) * 100
        kpis["latest_staff_ratio"] = float(ss.iloc[-1]["students_per_staff"])

    # --- Pillar scores latest (2026) ---
    if "the_ucar_rankings_wur_pillar_scores" in data:
        ps = data["the_ucar_rankings_wur_pillar_scores"]
        latest = ps[ps["year"] == ps["year"].max()]
        kpis["pillar_latest_year"] = int(ps["year"].max())
        # Overall pillar scores
        overall = latest[latest["subject"] == "Overall"]
        kpis["overall_pillars"] = {
            row["pillar"]: float(row["score"]) for _, row in overall.iterrows()
        }
        # By subject
        by_subject = {}
        for subj in latest["subject"].unique():
            subj_df = latest[latest["subject"] == subj]
            by_subject[subj] = {
                row["pillar"]: float(row["score"]) for _, row in subj_df.iterrows()
            }
        kpis["pillar_by_subject"] = by_subject

    # --- Subject rankings ---
    if "the_ucar_rankings_subject_rankings" in data:
        sr = data["the_ucar_rankings_subject_rankings"]
        kpis["subject_ranks"] = {
            row["subject"]: str(row["rank_display"]) for _, row in sr.iterrows()
        }

    # --- Impact rankings (latest year) ---
    if "the_ucar_rankings_impact_rankings" in data:
        ir = data["the_ucar_rankings_impact_rankings"]
        latest_year = ir["year"].max()
        latest_ir = ir[ir["year"] == latest_year]
        kpis["impact_latest_year"] = int(latest_year)
        kpis["impact_scores"] = {
            row["sdg"]: (float(row["score_lower"]), float(row["score_higher"]))
            for _, row in latest_ir.iterrows() if pd.notna(row.get("score_lower"))
        }

    # --- Research labs ---
    if "ucar_data_research" in data:
        labs = data["ucar_data_research"]
        kpis["research_lab_count"] = len(labs)

    # --- Subjects taught ---
    if "the_ucar_rankings_subjects_taught" in data:
        st = data["the_ucar_rankings_subjects_taught"]
        kpis["subjects_taught_count"] = len(st)

    return kpis

# ---------------------------------------------------------------------------
# 4. PLOTLY KPI DASHBOARDS
# ---------------------------------------------------------------------------
def build_kpi_dashboard(kpis, data):
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "Student Enrollment Trend",
            "Female vs International Student %",
            "2026 Overall Pillar Scores",
            "Subject Comparison Radar (2026)",
            "Impact Rankings SDG Scores",
            "Key Metrics Summary",
        ),
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "bar"}, {"type": "scatterpolar"}],
            [{"type": "bar"}, {"type": "indicator"}],
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )

    # --- Row 1, Col 1: Student Enrollment ---
    if "student_growth" in kpis:
        sg = kpis["student_growth"]
        fig.add_trace(go.Scatter(
            x=sg["years"], y=sg["total_students"],
            mode='lines+markers',
            name='Total Students',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=sg["years"], y=sg["staff_ratio"],
            mode='lines+markers',
            name='Students/Staff',
            line=dict(color='#ff7f0e', width=2, dash='dash'),
            yaxis='y2',
        ), row=1, col=1)
        fig.update_yaxes(title_text="Students", row=1, col=1)

    # --- Row 1, Col 2: Female vs International % ---
    if "student_growth" in kpis:
        sg = kpis["student_growth"]
        fig.add_trace(go.Scatter(
            x=sg["years"], y=sg["female_pct"],
            mode='lines+markers',
            name='Female %',
            line=dict(color='#e377c2', width=3),
            marker=dict(size=8),
        ), row=1, col=2)
        fig.add_trace(go.Scatter(
            x=sg["years"], y=sg["intl_pct"],
            mode='lines+markers',
            name='International %',
            line=dict(color='#2ca02c', width=3),
            marker=dict(size=8),
        ), row=1, col=2)
        fig.update_yaxes(title_text="Percentage", row=1, col=2)

    # --- Row 2, Col 1: Overall Pillar Scores Bar ---
    if "overall_pillars" in kpis:
        pillars = kpis["overall_pillars"]
        categories = list(pillars.keys())
        values = list(pillars.values())
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        fig.add_trace(go.Bar(
            x=categories, y=values,
            marker_color=colors[:len(categories)],
            text=[f"{v:.1f}" for v in values],
            textposition='outside',
            name='Pillar Score',
        ), row=2, col=1)
        fig.update_yaxes(title_text="Score", range=[0, 60], row=2, col=1)

    # --- Row 2, Col 2: Radar Chart (subjects comparison) ---
    if "pillar_by_subject" in kpis:
        by_subj = kpis["pillar_by_subject"]
        # Use Overall + top 4 subjects for readability
        subjects_to_plot = [s for s in by_subj.keys() if s != "Overall"][:4]
        if "Overall" in by_subj:
            subjects_to_plot = ["Overall"] + subjects_to_plot
        # Get common pillars
        common_pillars = None
        for s in subjects_to_plot:
            if common_pillars is None:
                common_pillars = set(by_subj[s].keys())
            else:
                common_pillars &= set(by_subj[s].keys())
        common_pillars = sorted(common_pillars) if common_pillars else []
        radar_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        for i, subj in enumerate(subjects_to_plot):
            vals = [by_subj[subj].get(p, 0) for p in common_pillars]
            fig.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=common_pillars + [common_pillars[0]],
                fill='toself',
                name=subj,
                line=dict(color=radar_colors[i % len(radar_colors)], width=2),
                opacity=0.3,
            ), row=2, col=2)
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 60])),
            polar2=dict(radialaxis=dict(visible=True, range=[0, 60])),
        )

    # --- Row 3, Col 1: Impact Rankings SDG ---
    if "impact_scores" in kpis:
        sdgs = list(kpis["impact_scores"].keys())[:15]  # cap
        lower = [kpis["impact_scores"][s][0] for s in sdgs]
        upper = [kpis["impact_scores"][s][1] for s in sdgs]
        mid = [(l + u) / 2 for l, u in zip(lower, upper)]
        fig.add_trace(go.Bar(
            x=sdgs, y=mid,
            error_y=dict(type='data', symmetric=False, array=[u - m for u, m in zip(upper, mid)],
                         arrayminus=[m - l for m, l in zip(mid, lower)]),
            marker_color='#e377c2',
            name='SDG Score',
        ), row=3, col=1)
        fig.update_xaxes(tickangle=45, row=3, col=1)

    # --- Row 3, Col 2: Indicator cards ---
    indicators = []
    if "latest_students" in kpis:
        indicators.append(("Students", kpis["latest_students"], 50000))
    if "latest_female_pct" in kpis:
        indicators.append(("Female %", kpis["latest_female_pct"], 100))
    if "latest_intl_pct" in kpis:
        indicators.append(("Intl %", kpis["latest_intl_pct"], 10))
    if "research_lab_count" in kpis:
        indicators.append(("Labs", kpis["research_lab_count"], 100))
    if "subjects_taught_count" in kpis:
        indicators.append(("Subjects", kpis["subjects_taught_count"], 50))

    for i, (title, val, max_val) in enumerate(indicators[:3]):
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=val,
            title=dict(text=title, font=dict(size=14)),
            gauge=dict(
                axis=dict(range=[0, max_val]),
                bar=dict(color='#2ca02c'),
                bgcolor='white',
                borderwidth=1,
                steps=[dict(range=[0, max_val * 0.6], color='#f0f0f0'),
                       dict(range=[max_val * 0.6, max_val], color='#d0e8d0')],
            ),
            domain=dict(x=[0 + i * 0.33, 0.28 + i * 0.33], y=[0, 0.9]),
        ), row=3, col=2)

    fig.update_layout(
        height=1400,
        width=1300,
        title_text="UCAR KPI Dashboard — University of Carthage",
        title_x=0.5,
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.05, xanchor='center', x=0.5),
    )
    return fig

# ---------------------------------------------------------------------------
# 5. MAIN
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("UCAR KNOWLEDGE GRAPH & KPI DASHBOARD GENERATOR")
    print("=" * 60)

    # Load data
    data = load_all_csvs()
    if not data:
        print("No CSV files found. Exiting.")
        return

    # Build knowledge graph
    kg = KnowledgeGraph()
    kg.build_from_data(data)

    # Compute KPIs
    kpis = compute_kpis(data)
    print(f"\nComputed {len(kpis)} KPI categories")

    # Save KPI summary JSON
    summary_file = os.path.join(CSV_DIR, "kpi_summary.json")
    # Convert numpy types for JSON serialization
    def convert(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(convert(kpis), f, indent=2, ensure_ascii=False)
    print(f"Saved KPI summary: {summary_file}")

    # Generate knowledge graph visualization
    net_fig = kg.to_plotly_network()
    net_html = os.path.join(CSV_DIR, "knowledge_graph.html")
    net_fig.write_html(net_html, include_plotlyjs='cdn')
    print(f"Saved knowledge graph: {net_html}")

    # Generate KPI dashboard
    kpi_fig = build_kpi_dashboard(kpis, data)
    kpi_html = os.path.join(CSV_DIR, "kpi_dashboard.html")
    kpi_fig.write_html(kpi_html, include_plotlyjs='cdn')
    print(f"Saved KPI dashboard: {kpi_html}")

    print("\n" + "=" * 60)
    print("DONE. Open the HTML files in your browser:")
    print(f"  - {net_html}")
    print(f"  - {kpi_html}")
    print("=" * 60)


if __name__ == "__main__":
    main()
