import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update st.tabs
old_tabs = """st.tabs([
    "Executive Overview", 
    "Institutional Analytics", 
    "Accreditation Status", 
    "Research & Faculty", 
    "Employment & Success", 
    "System Alerts", 
    "AI Strategic Assistant",
    "Institution Deep Dive",
    "Global THE Rankings",
    " Ranking Advisor"
])"""

new_tabs = """st.tabs([
    "Executive Overview", 
    "Institutional Analytics", 
    "Accreditation Status", 
    "Research & Faculty", 
    "Employment & Success", 
    "System Alerts", 
    "AI Strategic Assistant",
    "Institution Deep Dive",
    "Global THE Rankings",
    " Ranking Advisor",
    "Ranking Simulator"
])"""

if old_tabs in content:
    content = content.replace(old_tabs, new_tabs)
else:
    print("Warning: old tabs not found, maybe already updated")

new_tab_code = """

# --- RANKING SIMULATOR TAB ---
with tabs[10]:
    import plotly.graph_objects as go
    
    st.markdown("### Ranking Simulator (THE Scores)")
    st.markdown("Simulate the impact of strategic improvements on the Times Higher Education (THE) global ranking.")
    
    # SECTION 1: Current Scores Display
    st.markdown("#### Current Baseline (University of Carthage)")
    st_cols = st.columns(5)
    with st_cols[0]:
        st.markdown(create_kpi_card("Teaching", "20.1"), unsafe_allow_html=True)
    with st_cols[1]:
        st.markdown(create_kpi_card("Research Env", "9.7"), unsafe_allow_html=True)
    with st_cols[2]:
        st.markdown(create_kpi_card("Research Quality", "42.1"), unsafe_allow_html=True)
    with st_cols[3]:
        st.markdown(create_kpi_card("Industry", "36.9"), unsafe_allow_html=True)
    with st_cols[4]:
        st.markdown(create_kpi_card("International", "39.7"), unsafe_allow_html=True)
        
    st.markdown("---")
    
    # SECTION 2: Interactive Sliders
    st.markdown("#### Adjust Scores to Simulate New Rank")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        sim_teaching = st.slider("Teaching Score", min_value=20.1, max_value=100.0, value=20.1, step=0.1, key="sim_teaching")
        sim_research_env = st.slider("Research Environment", min_value=9.7, max_value=100.0, value=9.7, step=0.1, key="sim_research_env")
        sim_research_q = st.slider("Research Quality", min_value=42.1, max_value=100.0, value=42.1, step=0.1, key="sim_research_q")
        sim_industry = st.slider("Industry Score", min_value=36.9, max_value=100.0, value=36.9, step=0.1, key="sim_industry")
        sim_international = st.slider("International Outlook", min_value=39.7, max_value=100.0, value=39.7, step=0.1, key="sim_international")
        
        # Calculate improvement deltas
        d_teaching = sim_teaching - 20.1
        d_research_env = sim_research_env - 9.7
        d_research_q = sim_research_q - 42.1
        d_industry = sim_industry - 36.9
        d_international = sim_international - 39.7
        total_delta = d_teaching + d_research_env + d_research_q + d_industry + d_international
        
    with col2:
        # SECTION 6: Radar Chart Comparison
        categories = ['Teaching', 'Research Env', 'Research Quality', 'Industry', 'International']
        current_vals = [20.1, 9.7, 42.1, 36.9, 39.7]
        simulated_vals = [sim_teaching, sim_research_env, sim_research_q, sim_industry, sim_international]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=current_vals, theta=categories, fill='toself',
            name='Current', line_color='#6366f1', opacity=0.6))
        fig_radar.add_trace(go.Scatterpolar(
            r=simulated_vals, theta=categories, fill='toself',
            name='Simulated', line_color='#10b981', opacity=0.6))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,100])),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=40, t=20, b=20)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # SECTION 3: Estimated Rank Calculation
    composite_score = (
        sim_teaching * 0.29 +
        sim_research_env * 0.10 +
        sim_research_q * 0.29 +
        sim_industry * 0.04 +
        sim_international * 0.08
    )

    if composite_score >= 70: estimated_rank = "Top 200"
    elif composite_score >= 60: estimated_rank = "201-400"
    elif composite_score >= 50: estimated_rank = "401-600"
    elif composite_score >= 40: estimated_rank = "601-800"
    elif composite_score >= 30: estimated_rank = "801-1000"
    elif composite_score >= 22: estimated_rank = "1001-1250"
    elif composite_score >= 18: estimated_rank = "1251-1500"
    else: estimated_rank = "1501+"

    # Color logic
    if estimated_rank != "1501+":
        rank_color = "#10b981" # Green
    else:
        rank_color = "#f59e0b" if total_delta > 0 else "#ef4444" # Orange or Red
        
    st.markdown("### Simulated Results")
    res_cols = st.columns(3)
    with res_cols[0]:
        st.markdown(create_kpi_card("Current Rank", "1501+"), unsafe_allow_html=True)
    with res_cols[1]:
        st.markdown(f'''
        <div class="kpi-card" style="border: 2px solid {rank_color};">
            <div class="kpi-title">Simulated Rank</div>
            <div class="kpi-value" style="color: {rank_color};">{estimated_rank}</div>
        </div>
        ''', unsafe_allow_html=True)
    with res_cols[2]:
        st.markdown(create_kpi_card("Composite Score", f"{composite_score:.1f} / 100"), unsafe_allow_html=True)

    st.markdown(f"**Total Improvement:** <span style='color:#10b981;'>+{total_delta:.1f} points</span>", unsafe_allow_html=True)
    
    # SECTION 4: Required Actions per Criterion
    if total_delta > 0:
        st.markdown("#### Required Interventions")
        if d_teaching > 0:
            st.info(f"**Teaching (+{d_teaching:.1f} pts) :** Hire additional professors, reduce student/staff ratio.")
        if d_research_env > 0:
            st.info(f"**Research Environment (+{d_research_env:.1f} pts) :** Invest in lab infrastructure, recruit senior researchers.")
        if d_research_q > 0:
            st.info(f"**Research Quality (+{d_research_q:.1f} pts) :** Publish more papers in Q1 journals, secure international research grants.")
        if d_industry > 0:
            st.info(f"**Industry (+{d_industry:.1f} pts) :** Sign new industry partnerships, launch commercial internship programs.")
        if d_international > 0:
            st.info(f"**International Outlook (+{d_international:.1f} pts) :** Increase Erasmus agreements, recruit international students.")

    # SECTION 5: AI Strategic Analysis Button
    st.markdown("---")
    st.markdown("#### AI Roadmap Generator")
    if st.button("Generate AI Roadmap for this simulation", key="btn_sim_roadmap"):
        prompt = (
            f"Based on these target THE scores: Teaching: {sim_teaching:.1f}, Research Env: {sim_research_env:.1f}, "
            f"Research Quality: {sim_research_q:.1f}, Industry: {sim_industry:.1f}, International: {sim_international:.1f}. "
            f"The University of Carthage wants to go from rank 1501+ to {estimated_rank}. "
            f"Generate a precise 12-month action plan in French with: "
            f"1. Top 3 priority actions with deadlines "
            f"2. Required budget investment estimate in TND "
            f"3. Which institutions in the UCAR network should lead each action "
            f"4. Expected rank improvement timeline (quarterly). "
            f"Be specific, quantitative, and executive-level."
        )
        
        with st.spinner("Generating AI Roadmap via Grok..."):
            response = ask_grok(prompt)
            st.markdown("### 🤖 Grok AI Action Plan")
            st.markdown(f'''
            <div style="background:#1E1E2E; padding:20px; border-radius:8px; border:1px solid rgba(16,185,129,0.3);">
                {response}
            </div>
            ''', unsafe_allow_html=True)
"""

if "RANKING SIMULATOR TAB" not in content:
    content = content + new_tab_code
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully added new tab!")
else:
    print("Tab already exists!")
