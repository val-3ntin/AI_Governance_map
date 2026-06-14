import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# ─── PAGE CONFIGURATION & CORPORATE THEME ──────────────────────────────────────
st.set_page_config(page_title="AI Governance Strategic Engine | Italy", layout="wide")

# Custom CSS for an ultra-clean corporate presentation style
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1A1A1A;
    }
    .stApp {
        background-color: #FFFFFF;
    }
    /* Executive KPI Cards */
    .kpi-card {
        background-color: #F8F9FA;
        border-left: 5px solid #002B49;
        padding: 20px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .kpi-card.alert {
        border-left: 5px solid #E63946;
    }
    .kpi-title {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #5A6A85;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: #002B49;
    }
    .kpi-value.alert {
        color: #E63946;
    }
    .kpi-subtitle {
        font-size: 12px;
        color: #7A8B9E;
        margin-top: 4px;
    }
    /* Strategy Matrix Cards */
    .strategy-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .badge-do {
        background-color: #EBFFFA;
        color: #00A389;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        margin-bottom: 10px;
    }
    .badge-not {
        background-color: #FFEBEB;
        color: #E63946;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 12px;
        display: inline-block;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_index=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("<p style='color: #002B49; font-size: 28px; font-weight: 700; margin-bottom: 5px;'>Italy AI Governance: Strategic Decision Engine</p>", unsafe_allow_index=True)
st.markdown("<p style='color: #555555; font-size: 14px; margin-bottom: 25px;'>Stress-testing public administration adoption, regulatory latency, and institutional structural drivers under the 2024-2026 National Strategy.</p>", unsafe_allow_index=True)

# ─── DATA SETUP ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    weights = {
        'ongoing_enforcement': 1.0,
        'active_soft':         0.7,
        'one_off_position':    0.4,
        'expired_dormant':     0.1,
    }

    data = {
        'Garante (DPA)': {
            'Risk_Auditing': {'mandate':1,'activity_type':'ongoing_enforcement','last_year':2025,'reach':1},
            'Data_Privacy':  {'mandate':1,'activity_type':'ongoing_enforcement','last_year':2025,'reach':1},
            'SME_Sandboxes': {'mandate':0,'activity_type':'one_off_position',   'last_year':2023,'reach':0},
            'Transparency':  {'mandate':1,'activity_type':'active_soft',        'last_year':2024,'reach':0},
            'Funding_Grants':{'mandate':0,'activity_type':'one_off_position',   'last_year':2023,'reach':0},
        },
        'AgID': {
            'Risk_Auditing': {'mandate':1,'activity_type':'active_soft','last_year':2024, 'reach':0},
            'Data_Privacy':  {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':0},
            'SME_Sandboxes': {'mandate':0,'activity_type':'active_soft','last_year':2024, 'reach':0},
            'Transparency':  {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':0},
            'Funding_Grants':{'mandate':1,'activity_type':'ongoing_enforcement','last_year':2025,'reach':0},
        },
        'CDP': {
            'Risk_Auditing': {'mandate':0,'activity_type':'expired_dormant','last_year':2021,'reach':0},
            'Data_Privacy':  {'mandate':0,'activity_type':'expired_dormant','last_year':2021,'reach':0},
            'SME_Sandboxes': {'mandate':0,'activity_type':'active_soft',   'last_year':2024,'reach':0},
            'Transparency':  {'mandate':0,'activity_type':'expired_dormant','last_year':2022,'reach':0},
            'Funding_Grants':{'mandate':1,'activity_type':'ongoing_enforcement','last_year':2025,'reach':1},
        },
        'Corte dei Conti': {
            'Risk_Auditing': {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':1},
            'Data_Privacy':  {'mandate':0,'activity_type':'one_off_position','last_year':2022,'reach':0},
            'SME_Sandboxes': {'mandate':0,'activity_type':'expired_dormant','last_year':2020,'reach':0},
            'Transparency':  {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':0},
            'Funding_Grants':{'mandate':1,'activity_type':'ongoing_enforcement','last_year':2025,'reach':1},
        },
        'Lombardy Region': {
            'Risk_Auditing': {'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
            'Data_Privacy':  {'mandate':0,'activity_type':'active_soft','last_year':2024,'reach':0},
            'SME_Sandboxes': {'mandate':1,'activity_type':'ongoing_enforcement','last_year':2025,'reach':1},
            'Transparency':  {'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
            'Funding_Grants':{'mandate':1,'activity_type':'ongoing_enforcement','last_year':2025,'reach':1},
        },
        'Confindustria Digitale': {
            'Risk_Auditing': {'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
            'Data_Privacy':  {'mandate':0,'activity_type':'active_soft',    'last_year':2024,'reach':0},
            'SME_Sandboxes': {'mandate':0,'activity_type':'active_soft',    'last_year':2024,'reach':0},
            'Transparency':  {'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
            'Funding_Grants':{'mandate':0,'activity_type':'active_soft',    'last_year':2024,'reach':0},
        },
        'SME Networks (PMI)': {
            'Risk_Auditing': {'mandate':0,'activity_type':'expired_dormant','last_year':2020,'reach':0},
            'Data_Privacy':  {'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
            'SME_Sandboxes': {'mandate':0,'activity_type':'expired_dormant','last_year':2022,'reach':0},
            'Transparency':  {'mandate':0,'activity_type':'expired_dormant','last_year':2021,'reach':0},
            'Funding_Grants':{'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
        },
        'CDP Venture Capital': {
            'Risk_Auditing': {'mandate':0,'activity_type':'expired_dormant','last_year':2021,'reach':0},
            'Data_Privacy':  {'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
            'SME_Sandboxes': {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':1},
            'Transparency':  {'mandate':0,'activity_type':'expired_dormant','last_year':2022,'reach':0},
            'Funding_Grants':{'mandate':1,'activity_type':'ongoing_enforcement','last_year':2025,'reach':1},
        },
        'Altroconsumo': {
            'Risk_Auditing': {'mandate':0,'activity_type':'active_soft','last_year':2024,'reach':0},
            'Data_Privacy':  {'mandate':1,'activity_type':'active_soft','last_year':2025,'reach':1},
            'SME_Sandboxes': {'mandate':0,'activity_type':'expired_dormant','last_year':2021,'reach':0},
            'Transparency':  {'mandate':1,'activity_type':'active_soft','last_year':2025,'reach':1},
            'Funding_Grants':{'mandate':0,'activity_type':'expired_dormant','last_year':2020,'reach':0},
        },
        'Trade Unions (CGIL/CISL/UIL)': {
            'Risk_Auditing': {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':1},
            'Data_Privacy':  {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':0},
            'SME_Sandboxes': {'mandate':0,'activity_type':'expired_dormant','last_year':2021,'reach':0},
            'Transparency':  {'mandate':1,'activity_type':'active_soft','last_year':2025,'reach':1},
            'Funding_Grants':{'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
        },
        'AIxIA': {
            'Risk_Auditing': {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':0},
            'Data_Privacy':  {'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
            'SME_Sandboxes': {'mandate':0,'activity_type':'active_soft','last_year':2024,'reach':0},
            'Transparency':  {'mandate':1,'activity_type':'active_soft','last_year':2025,'reach':0},
            'Funding_Grants':{'mandate':0,'activity_type':'active_soft','last_year':2024,'reach':0},
        },
        'Fondazione Leonardo': {
            'Risk_Auditing': {'mandate':0,'activity_type':'active_soft',    'last_year':2024,'reach':0},
            'Data_Privacy':  {'mandate':0,'activity_type':'one_off_position','last_year':2023,'reach':0},
            'SME_Sandboxes': {'mandate':0,'activity_type':'expired_dormant','last_year':2021,'reach':0},
            'Transparency':  {'mandate':0,'activity_type':'active_soft',    'last_year':2024,'reach':0},
            'Funding_Grants':{'mandate':1,'activity_type':'active_soft',    'last_year':2025,'reach':0},
        },
    }
    return data, weights

structured_data, ACTIVITY_WEIGHTS = load_data()
pillars = ['Risk_Auditing', 'Data_Privacy', 'SME_Sandboxes', 'Transparency', 'Funding_Grants']
actors = list(structured_data.keys())

# ─── SIDEBAR DESIGN ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<p style='font-size: 18px; font-weight: 700; color: #002B49; margin-bottom: 5px;'>Simulation Controls</p>", unsafe_allow_index=True)
    st.markdown("Modify baseline structural constraints to stress-test ecosystem metrics.")
    st.divider()
    
    selected_pillar = st.selectbox("Strategic Metric", options=pillars, format_func=lambda x: x.replace('_', ' '))
    sim_year = st.slider("Simulation Horizon", min_value=2023, max_value=2030, value=2026, step=1)
    decay_base = st.slider("Dormancy Decay Factor", min_value=0.50, max_value=1.00, value=0.88, step=0.01, 
                           help="Calculates policy obsolescence. At 0.88, static portfolios lose ~12% structural efficiency annually if enforcement stays dormant.")

# ─── COMPUTE ENGINE ──────────────────────────────────────────────────────────
simulated_scores = {}
for actor in actors:
    cell = structured_data[actor][selected_pillar]
    activity_w = ACTIVITY_WEIGHTS[cell['activity_type']]
    reach_bonus = 1 + cell['reach']
    raw = cell['mandate'] + activity_w * reach_bonus
    years_stale = max(0, sim_year - cell['last_year'])
    score = min(3.0, round(raw * (decay_base ** years_stale), 2))
    simulated_scores[actor] = score

s_series = pd.Series(simulated_scores).sort_values(ascending=True)

# ─── EXECUTIVE KPI CARD CONTAINER ────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Avg Portfolio Readiness</div>
            <div class='kpi-value'>{s_series.mean():.2f} / 3.00</div>
            <div class='kpi-subtitle'>Simulated global system mean</div>
        </div>
    """, unsafe_allow_index=True)
with col2:
    st.markdown(f"""
        <div class='kpi-card alert'>
            <div class='kpi-title'>Maximum Systemic Risk</div>
            <div class='kpi-value alert'>{s_series.index[0]}</div>
            <div class='kpi-subtitle'>Lowest metric output capacity</div>
        </div>
    """, unsafe_allow_index=True)
with col3:
    st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Ecosystem Anchor Partner</div>
            <div class='kpi-value'>{s_series.index[-1]}</div>
            <div class='kpi-subtitle'>Highest functional capacity cell</div>
        </div>
    """, unsafe_allow_index=True)

st.markdown("<br>", unsafe_allow_index=True)

# ─── ANALYTICAL WORKSPACES ───────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Capacity Delta Profile", "🏁 Matrix Analytics", "♟️ Strategic Playbooks"])

with tab1:
    clean_pillar_name = selected_pillar.replace('_', ' ')
    
    # Render Matplotlib Figure with strict minimalist styling
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor='#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    colors = ['#E63946' if i == 0 else '#002B49' for i in range(len(s_series))]
    bars = ax.barh(s_series.index, s_series.values, color=colors, height=0.55)

    for bar, val in zip(bars, s_series.values):
        ax.text(val + 0.04, bar.get_y() + bar.get_height()/2, 
                f'{val:.2f}', va='center', fontweight='bold', 
                color=bar.get_facecolor(), fontsize=10)
        
    ax.set_xlim(0, 3.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', length=0)
    ax.set_xticks([])
    ax.set_yticklabels(s_series.index, fontsize=10.5, fontweight='500', color='#2C2C2A')

    fig.text(0.02, 0.96, f"Structural Decay Simulation: {clean_pillar_name}", fontsize=14, fontweight='bold', color='#111111')
    fig.text(0.02, 0.90, f"Simulated systemic capacity in {sim_year} accounting for historical performance stagnation.", fontsize=10.5, color='#555555')

    plt.tight_layout()
    st.pyplot(fig)

with tab2:
    st.markdown("<p style='font-size: 16px; font-weight: 700; color: #111111;'>Dynamic Matrix Cross-Reference</p>", unsafe_allow_index=True)
    st.markdown("<p style='font-size: 13px; color: #555555;'>This system architecture matrix updates dynamically as simulation parameters shift. Red indicators represent prioritized non-profit intervention fields.</p>", unsafe_allow_index=True)
    
    heatmap_data = []
    for actor in actors:
        actor_scores = {}
        for p in pillars:
            cell = structured_data[actor][p]
            raw = cell['mandate'] + ACTIVITY_WEIGHTS[cell['activity_type']] * (1 + cell['reach'])
            years_stale = max(0, sim_year - cell['last_year'])
            actor_scores[p] = min(3.0, round(raw * (decay_base ** years_stale), 2))
        heatmap_data.append(actor_scores)
        
    df_heat = pd.DataFrame(heatmap_data, index=actors)

    fig2, ax2 = plt.subplots(figsize=(11, 6.5), facecolor='#FFFFFF')
    ax2.set_facecolor('#FFFFFF')
    
    prof_cmap = LinearSegmentedColormap.from_list(
        'corporate_blue', ['#F8F9FA', '#B9D1EA', '#5A88B5', '#0C2C52'], N=256
    )

    sns.heatmap(
        df_heat,
        ax=ax2, 
        cmap=prof_cmap, 
        vmin=0, vmax=3,
        annot=True, 
        fmt='.1f',
        annot_kws={'size': 11, 'weight': 'bold'},
        linewidths=3,
        linecolor='white',
        cbar=False            
    )

    ax2.xaxis.tick_top()
    ax2.xaxis.set_label_position('top')
    ax2.tick_params(left=False, top=False, bottom=False)

    clean_headers = [p.replace('_', ' ') for p in pillars]
    ax2.set_xticklabels(clean_headers, rotation=0, ha='center', fontsize=10, fontweight='bold', color='#333333')
    ax2.set_yticklabels(df_heat.index, rotation=0, fontsize=10.5, fontweight='500', color='#333333')

    flags = [(6, 2), (2, 0), (6, 3), (11, 2), (8, 2), (4, 3)]
    for (y, x) in flags:
        ax2.plot(x + 0.85, y + 0.15, marker='o', markersize=8, color='#E63946', markeredgecolor='white')

    plt.tight_layout()
    st.pyplot(fig2)
    
with tab3:
    st.markdown("<p style='font-size: 16px; font-weight: 700; color: #111111;'>Strategic Arbitrage & Capital Deployment Playbooks</p>", unsafe_allow_index=True)
    st.markdown("<p style='font-size: 13.5px; color: #555555;'>Cross-referencing legal mandates against structural funding pipelines isolates three key intervention vectors. Philanthropic grants should bypass standard regulatory lobbying and align with these operational levers.</p>", unsafe_allow_index=True)
    st.divider()

    # ─── PLAYBOOK 1 ──────────────────────────────────────────────────────────
    st.markdown("""
        <div class='strategy-card'>
            <div class='badge-do'>RECOMMENDED STRATEGY</div>
            <p style='font-size: 15px; font-weight: 700; color: #002B49; margin-top:5px; margin-bottom:5px;'>1. Force SME Algorithmic Transparency via National Labor Contracts</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Vulnerability:</b> While SME Networks (PMI) maintain non-existent transparency and sandbox scores (0.1), Italy's business infrastructure relies natively on high-trust informal local relationships, heavily resisting top-down regulatory reporting dictates from Rome.</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Execution Vector:</b> Do not build open-source transparency toolkits for business entities. Instead, deploy grants to partner with major <b>Trade Unions (CGIL/CISL/UIL)</b>. Unions hold a robust 2.4 capacity on System Transparency. By writing algorithmic explainability mandates directly into National Collective Labor Agreements (CCNL), non-profits force legally binding operational compliance via established worker rights, entirely bypassing corporate friction.</p>
        </div>
    """, unsafe_allow_index=True)

    # ─── PLAYBOOK 2 ──────────────────────────────────────────────────────────
    st.markdown("""
        <div class='strategy-card'>
            <div class='badge-do'>RECOMMENDED STRATEGY</div>
            <p style='font-size: 15px; font-weight: 700; color: #002B49; margin-top:5px; margin-bottom:5px;'>2. Embed Safety Conditionality inside the €30B CDP Funding Pipeline</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Vulnerability:</b> Cassa Depositi e Prestiti (CDP) commands maximum capital deployment leverage (3.0) but runs a near-zero internal AI risk auditing capability (0.1). Italy's promotional banking tradition prioritizes macroeconomic transition speed over risk oversight, creating an unmonitored capital pipeline.</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Execution Vector:</b> Do not lobby the national data protection authority to curb financial lines. Instead, launch a capital-conditionality campaign targeting <b>CDP Venture Capital</b>. Because they maintain an active 2.1 footprint in SME Innovation Sandboxes, philanthropists can design and lobby for mandatory 'AI Safety Due Diligence' criteria, embedding compliance parameters directly into the deployment terms of deep-tech venture funds.</p>
        </div>
    """, unsafe_allow_index=True)

    # ─── PLAYBOOK 3 ──────────────────────────────────────────────────────────
    st.markdown("""
        <div class='strategy-card'>
            <div class='badge-not'>COUNTER-RECOMMENDED LOBBYING</div>
            <p style='font-size: 15px; font-weight: 700; color: #E63946; margin-top:5px; margin-bottom:5px;'>3. Avoid Centralized Registries — Bridge the Rome-Regional Divide Instead</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Structural Trap:</b> Italy's constitutional architecture creates a deep disconnect: central regulators in Rome (Garante, AgID) possess broad statutory oversight mandates but lack operational budget lines, while wealthy northern regions (Lombardy Region, scoring 3.0 on sandboxes) hold cash reserves but operate completely untethered from centralized safety frameworks.</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Execution Vector:</b> Do not advocate for centralized registries or unified federal mandates; these initiatives trigger constitutional gridlock and are functionally ignored. Instead, use capital to place civil society technologists as 'transparency embeds' inside active regional sandbox hubs, validating Rome's standards through regional execution power.</p>
        </div>
    """, unsafe_allow_index=True)
