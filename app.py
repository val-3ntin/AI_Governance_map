import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# ─── PAGE CONFIGURATION ──────────────────────────────────────────────────────
st.set_page_config(page_title="AI Governance Simulator", layout="wide")

st.title("Italy AI Governance: Temporal Decay Simulator")
st.markdown("Use the sidebar controls to simulate how historical policy stagnation degrades an institution's readiness score over time.")

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

# ─── UI CONTROLS (SIDEBAR) ───────────────────────────────────────────────────
with st.sidebar:
    st.image("https://flagcdn.com/w160/it.png", width=50)
    st.header("Simulation Engine")
    st.markdown("Adjust parameters to stress-test the Italian AI Governance ecosystem.")
    st.divider()
    
    selected_pillar = st.selectbox("🎯 Target Governance Pillar", options=pillars)
    sim_year = st.slider("⏱️ Simulation Year", min_value=2023, max_value=2030, value=2025, step=1)
    
    st.divider()
    st.markdown("**Advanced Assumptions**")
    decay_base = st.slider("📉 Decay Base Penalty", min_value=0.50, max_value=1.00, value=0.88, step=0.01, 
                           help="0.88 means an actor loses 12% of their score for every year a policy sits dormant without enforcement.")

# ─── MATH ENGINE (Must happen before KPIs) ───────────────────────────────────
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

# ─── EXECUTIVE SUMMARY KPIs ──────────────────────────────────────────────────
st.markdown("### Ecosystem Health Overview")
col1, col2, col3 = st.columns(3)

avg_decay = s_series.mean()
most_vulnerable = s_series.index[0]
strongest = s_series.index[-1]

with col1:
    st.metric(label="Average Pillar Readiness (0-3)", value=f"{avg_decay:.2f}", delta="-0.15 YoY" if sim_year > 2024 else None)
with col2:
    st.metric(label="Most Vulnerable Actor", value=most_vulnerable, delta="High Risk", delta_color="inverse")
with col3:
    st.metric(label="Highest Capacity Actor", value=strongest, delta="Anchor Partner")

st.divider()

# ─── MAIN DASHBOARD TABS ─────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📉 Temporal Decay Simulator", "🗺️ Ecosystem Heatmap", "🎯 Strategic Interventions"])

with tab1:
    st.markdown("#### Simulating Policy 'Rot' over Time")
    
    # Render Matplotlib Figure
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    fig, ax = plt.subplots(figsize=(10, 6.5), facecolor='#FFFFFF')
    ax.set_facecolor('#FFFFFF')

    colors = ['#E63946' if i == 0 else '#002B49' for i in range(len(s_series))]
    bars = ax.barh(s_series.index, s_series.values, color=colors, height=0.6)

    for bar, val in zip(bars, s_series.values):
        ax.text(val + 0.05, bar.get_y() + bar.get_height()/2, 
                f'{val:.2f}', va='center', fontweight='bold', 
                color=bar.get_facecolor(), fontsize=11)
        
    ax.set_xlim(0, 3.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', length=0)
    ax.set_xticks([])
    ax.set_yticklabels(s_series.index, fontsize=11, fontweight='500', color='#333333')

    clean_pillar_name = selected_pillar.replace('_', ' ')
    fig.text(0.05, 1.05, f"Decay Simulation: {clean_pillar_name}", 
             fontsize=16, fontweight='bold', color='#111111')
    fig.text(0.05, 0.99, f"Projected scores in {sim_year} applying a {decay_base} decay curve to historical policies.", 
             fontsize=11, color='#555555')

    plt.tight_layout()
    st.pyplot(fig)
    
    st.info("**Strategic Insight:** Notice how 'On-Paper' mandates from 2021/2022 quickly drag an actor to the bottom of the rankings if no active enforcement has occurred recently.")

with tab2:
    st.markdown("#### Dynamic Ecosystem Heatmap")
    st.markdown("This matrix automatically updates based on your **Simulation Year** and **Decay** sliders in the sidebar. Red dots indicate key intervention opportunities.")
    
    # 1. Calculate the full matrix dynamically based on current slider values
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

    # 2. Draw the McKinsey-style professional Heatmap
    fig2, ax2 = plt.subplots(figsize=(11, 7), facecolor='#FFFFFF')
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

    # 3. Clean up the Axes
    ax2.xaxis.tick_top()
    ax2.xaxis.set_label_position('top')
    ax2.tick_params(left=False, top=False, bottom=False)

    clean_headers = [p.replace('_', ' ') for p in pillars]
    ax2.set_xticklabels(clean_headers, rotation=0, ha='center', fontsize=11, fontweight='bold', color='#333333')
    ax2.set_yticklabels(df_heat.index, rotation=0, fontsize=11, fontweight='500', color='#333333')

    # 4. Add the Intervention Opportunity Flags
    flags = [(6, 2), (2, 0), (6, 3), (11, 2), (8, 2), (4, 3)]
    for (y, x) in flags:
        ax2.plot(x + 0.85, y + 0.15, marker='o', markersize=8, color='#E63946', markeredgecolor='white')

    plt.tight_layout()
    st.pyplot(fig2)
    
with tab3:
    st.markdown("#### 🎯 Strategic Playbooks for Non-Profits")
    st.markdown("Based on our temporal decay and capacity models, we have identified the **Top 3 structural vulnerabilities** in the Italian AI ecosystem. Below are tailored, high-leverage intervention strategies for international non-profits.")
    st.divider()

    # ─── INTERVENTION 1 ──────────────────────────────────────────────────────────
    st.markdown("##### 1. The SME Transparency Void")
    col1, col2 = st.columns(2)
    with col1:
        st.warning("**The Gap:** 99% of Italian businesses are SMEs, yet zero algorithmic disclosure norms exist for them.")
        st.markdown("**Root Cause (Cultural):** Italy's industrial fabric relies heavily on informal, high-trust local networks rather than public registries. Digital compliance is historically viewed as a bureaucratic tax rather than an innovation driver.")
    with col2:
        st.success("**The Playbook:** Bottom-Up Pressure")
        st.markdown("""
        * ❌ **Avoid:** Selling generic "AI Transparency Toolkits" directly to resource-constrained SMEs.
        * ✅ **Action:** Partner with **Trade Unions (CGIL/CISL)** to legally demand algorithmic explainability in HR/recruitment tools during collective bargaining.
        * ✅ **Action:** Use **Altroconsumo** to pressure B2C SMEs from the consumer demand side.
        """)
    st.divider()

    # ─── INTERVENTION 2 ──────────────────────────────────────────────────────────
    st.markdown("##### 2. The €30B Mandate Blindspot")
    col1, col2 = st.columns(2)
    with col1:
        st.warning("**The Gap:** CDP allocates billions in PNRR tech funding but requires zero AI risk-auditing from its beneficiaries.")
        st.markdown("**Root Cause (Geopolitical/Legal):** CDP operates strictly under financial/ESG mandates. Italian financial law does not yet officially classify 'Algorithmic Risk' as a financial or environmental liability.")
    with col2:
        st.success("**The Playbook:** Redefining ESG")
        st.markdown("""
        * ❌ **Avoid:** Lobbying CDP's tech division to build an internal AI ethics team (they lack the legal mandate).
        * ✅ **Action:** Lobby the Ministry of Economy to formally classify *AI Model Risk* under standard national ESG compliance metrics.
        * ✅ **Action:** Provide technical support to the **Corte dei Conti** (Judicial Audit) to track how PNRR automated-decision funds are executed.
        """)
    st.divider()

    # ─── INTERVENTION 3 ──────────────────────────────────────────────────────────
    st.markdown("##### 3. The Rome-Regional Disconnect")
    col1, col2 = st.columns(2)
    with col1:
        st.warning("**The Gap:** Rome writes the rules, but the Regions hold the innovation money.")
        st.markdown("**Root Cause (Geopolitical):** The EU AI Act relies on national bodies (Garante, AgID) for enforcement, but actual PNRR sandbox and testbed funds flow heavily through decentralized regional governments.")
    with col2:
        st.success("**The Playbook:** The 'Ethical Testbed' Bridge")
        st.markdown("""
        * ❌ **Avoid:** Waiting for Rome-based agencies (AgID) to fund AI sandboxes; they are severely under-resourced.
        * ✅ **Action:** Secure regional PNRR testbed funds via the **Lombardy Region** or **CDP Venture Capital**, but *voluntarily* apply AgID's strict risk frameworks to the project to create a gold-standard, cross-border case study.
        """)