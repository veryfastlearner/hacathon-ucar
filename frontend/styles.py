import streamlit as st

def apply_global_styles():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #f4f6f9;
        }
        
        .stApp {
            background-color: #f4f6f9;
            color: #1e293b;
        }
        
        /* KPI Cards Styling */
        .kpi-card {
            background-color: #ffffff;
            border-radius: 6px;
            padding: 24px;
            margin: 12px 0;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #0f172a;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        }
        
        .kpi-title {
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 8px;
        }
        
        .kpi-value {
            font-size: 2rem;
            font-weight: 700;
            color: #0f172a;
        }
        
        /* Headers and Text */
        h1, h2, h3 {
            color: #0f172a !important;
            font-weight: 700 !important;
        }
        
        p {
            color: #334155;
        }
        
        /* Alerts Styling */
        .alert-card {
            background-color: #ffffff;
            border-radius: 6px;
            padding: 16px 24px;
            margin: 12px 0;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }
        
        .alert-danger {
            border-left: 4px solid #dc2626;
            background-color: #fef2f2;
        }
        
        .alert-warning {
            border-left: 4px solid #f59e0b;
            background-color: #fffbeb;
        }
        
        .alert-title {
            font-weight: 600;
            color: #0f172a;
            margin-bottom: 4px;
        }
        
        .alert-text {
            font-size: 0.9rem;
            color: #475569;
        }
        
        /* Tabs Customization */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
            color: #64748b;
        }

        .stTabs [aria-selected="true"] {
            color: #0f172a;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)
