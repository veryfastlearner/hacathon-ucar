import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_code = """
    st.markdown("---")
    st.markdown("### UCAR vs THE Benchmark Comparison")
    
    # STEP 1: THE Averages
    the_avg_teaching = (24.8 + 19.3) / 2
    the_avg_research_env = (10.2 + 9.4) / 2
    the_avg_research_quality = (32.2 + 44.6) / 2
    the_avg_industry = (34.7 + 28.1) / 2
    the_avg_international = (43.9 + 42.1) / 2
    
    # STEP 2: UCAR Internal KPIs
    import pandas as pd
    ucar_teaching = df['success_rate'].mean() * 100
    ucar_research = df['research_score'].mean()
    
    # Active projects proxy -> maps to research env (capped at 20 to stay realistic)
    active_sum = df['active_projects'].sum()
    if active_sum == 0:
        ucar_research_env = 0
    else:
        ucar_research_env = min((active_sum / (active_sum + 50)) * 20, 20)
        
    ucar_industry = df['employability_rate'].mean() * 100
    ucar_international = (df['publications'].sum() / len(df) / 10)
    
    # STEP 3: Comparison Table
    comp_data = {
        "Criterion": ["Teaching", "Research Env", "Research Quality", "Industry", "International"],
        "THE Average (First+Last)/2": [the_avg_teaching, the_avg_research_env, the_avg_research_quality, the_avg_industry, the_avg_international],
        "UCAR Internal": [ucar_teaching, ucar_research_env, ucar_research, ucar_industry, ucar_international]
    }
    comp_df = pd.DataFrame(comp_data)
    comp_df["Gap"] = comp_df["UCAR Internal"] - comp_df["THE Average (First+Last)/2"]
    
    def get_status(gap):
        if gap >= 0: return "✅ Above"
        elif gap >= -5: return "🟡 Close"
        else: return "🔴 Below"
        
    comp_df["Status"] = comp_df["Gap"].apply(get_status)
    
    st.dataframe(comp_df.style.format({
        "THE Average (First+Last)/2": "{:.1f}", 
        "UCAR Internal": "{:.1f}", 
        "Gap": "{:.1f}"
    }), use_container_width=True)
    
    # STEP 4: Bar Chart
    import plotly.express as px
    
    # Melt for plotly express grouped bar chart
    bar_df = pd.melt(comp_df, id_vars=['Criterion'], value_vars=['THE Average (First+Last)/2', 'UCAR Internal'],
                     var_name='Metric Type', value_name='Score')
                     
    fig_comp = px.bar(bar_df, x='Criterion', y='Score', color='Metric Type', barmode='group',
                      title="UCAR Internal Performance vs THE Benchmark (First & Last Average)",
                      color_discrete_map={"THE Average (First+Last)/2": "#6366f1", "UCAR Internal": "#10b981"})
    
    # Add horizontal lines
    for i, row in comp_df.iterrows():
        fig_comp.add_shape(type="line", x0=i-0.4, x1=i+0.4, y0=row["THE Average (First+Last)/2"], y1=row["THE Average (First+Last)/2"],
                           line=dict(color="red", width=2, dash="dash"))
                           
    fig_comp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_comp, use_container_width=True)
    
    # STEP 5: AI Insight Generation
    if st.button("Analyse les écarts avec l'IA", key="btn_gap_analysis"):
        prompt_gap = (
            f"Compare these scores:\\n"
            f" THE Benchmark averages (first+last category average):\\n"
            f" Teaching={the_avg_teaching:.1f}, Research Env={the_avg_research_env:.1f},\\n"
            f" Research Quality={the_avg_research_quality:.1f}, \\n"
            f" Industry={the_avg_industry:.1f}, International={the_avg_international:.1f}\\n\\n"
            f" UCAR Internal performance proxies:\\n"
            f" Teaching proxy={ucar_teaching:.1f}, \\n"
            f" Research proxy={ucar_research:.1f},\\n"
            f" Research Env proxy={ucar_research_env:.1f},\\n"
            f" Industry proxy={ucar_industry:.1f},\\n"
            f" International proxy={ucar_international:.1f}\\n\\n"
            f" Identify the 3 biggest gaps between UCAR internal performance \\n"
            f" and the THE benchmark. For each gap, explain in French:\\n"
            f" 1. Why this gap exists\\n"
            f" 2. What concrete action closes it fastest\\n"
            f" 3. Expected impact on THE ranking score\\n\\n"
            f" Be direct, quantitative, executive-level. Max 200 words."
        )
        with st.spinner("Analyse des écarts via Grok..."):
            response_gap = ask_grok(prompt_gap)
            st.info(response_gap)
            
    # STEP 6: Overall Match Score
    gaps = [
        abs(ucar_teaching - the_avg_teaching),
        abs(ucar_research - the_avg_research_quality),
        abs(ucar_research_env - the_avg_research_env),
        abs(ucar_industry - the_avg_industry),
        abs(ucar_international - the_avg_international)
    ]
    
    alignment_score = 100 - (sum(gaps) / len(gaps))
    alignment_score = max(0, min(100, alignment_score))
    
    if alignment_score >= 70: align_color = "#10b981"
    elif alignment_score >= 50: align_color = "#f59e0b"
    else: align_color = "#ef4444"
    
    st.markdown("---")
    st.markdown(f'''
    <div class="kpi-card" style="border: 2px solid {align_color}; text-align: center;">
        <div class="kpi-title" style="font-size: 16px;">Benchmark Alignment Score</div>
        <div class="kpi-value" style="color: {align_color}; font-size: 32px;">{alignment_score:.1f}/100</div>
    </div>
    ''', unsafe_allow_html=True)
"""

if "UCAR vs THE Benchmark Comparison" not in content:
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content + new_code)
    print("Added comparison section!")
else:
    print("Section already exists!")
