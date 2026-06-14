import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
import plotly.graph_objects as go

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Italy AI Governance Intelligence",
    page_icon="🇮🇹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── GLOBAL CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Sora', system-ui, sans-serif;
    color: #0D1B2A;
    background-color: #F7F8FA;
}
.stApp { background-color: #F7F8FA; }
.block-container { padding: 0 2rem 3rem 2rem; max-width: 1400px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #0D1B2A;
    border-right: 1px solid #1E3048;
}
section[data-testid="stSidebar"] * { color: #C8D8E8 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label { color: #7A99B8 !important; font-size: 11px !important; letter-spacing: .08em; text-transform: uppercase; }
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb] { background: #152235 !important; border-color: #2E4A66 !important; }
section[data-testid="stSidebar"] p { color: #7A99B8 !important; font-size: 12px !important; }

/* ── Nav tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1.5px solid #DDE2EA;
    gap: 0;
    padding: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Sora', sans-serif;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: .05em;
    text-transform: uppercase;
    color: #7A8EA6;
    padding: 10px 20px;
    border-bottom: 2px solid transparent;
    background: transparent;
    margin-bottom: -1.5px;
}
.stTabs [aria-selected="true"] {
    color: #0D1B2A !important;
    border-bottom: 2px solid #0072CE !important;
    background: transparent !important;
}

/* ── Metric tiles ── */
.metric-tile {
    background: #FFFFFF;
    border: 1px solid #DDE2EA;
    border-top: 3px solid #0072CE;
    padding: 18px 20px 16px;
    border-radius: 2px;
}
.metric-tile.alert { border-top-color: #E63946; }
.metric-tile.amber { border-top-color: #F5A623; }
.metric-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: #7A8EA6;
    margin-bottom: 6px;
    font-family: 'DM Mono', monospace;
}
.metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #0D1B2A;
    line-height: 1.1;
    font-family: 'DM Mono', monospace;
}
.metric-value.alert { color: #E63946; }
.metric-sub {
    font-size: 11px;
    color: #9BAABF;
    margin-top: 4px;
}

/* ── Strategy cards ── */
.s-card {
    background: #FFFFFF;
    border: 1px solid #DDE2EA;
    border-left: 3px solid #0072CE;
    padding: 22px 24px;
    margin-bottom: 16px;
    border-radius: 2px;
}
.s-card.red { border-left-color: #E63946; }
.s-card.amber { border-left-color: #F5A623; }
.badge {
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: .1em;
    text-transform: uppercase;
    padding: 3px 9px;
    border-radius: 2px;
    margin-bottom: 10px;
}
.badge.go   { background: #E8F4FD; color: #0072CE; }
.badge.stop { background: #FDECEE; color: #E63946; }
.badge.caution { background: #FEF6E8; color: #C4830A; }

/* ── Section header rule ── */
.section-rule {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 28px 0 18px;
}
.section-rule .label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: .15em;
    text-transform: uppercase;
    color: #7A8EA6;
    white-space: nowrap;
}
.section-rule .line {
    flex: 1;
    height: 1px;
    background: #DDE2EA;
}

/* ── Actor pin legend ── */
.pin-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 16px;
    margin-top: 12px;
}
.pin-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: #4A5E75;
}
.pin-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}

/* ── Landing hero ── */
.hero-wrap {
    background: #0D1B2A;
    margin: -16px -32px 0;
    padding: 48px 40px 40px;
    border-bottom: 1px solid #1E3048;
}
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: .2em;
    text-transform: uppercase;
    color: #0072CE;
    margin-bottom: 12px;
}
.hero-title {
    font-size: 36px;
    font-weight: 700;
    color: #F7F8FA;
    line-height: 1.15;
    max-width: 700px;
    margin-bottom: 14px;
}
.hero-title span { color: #0072CE; }
.hero-body {
    font-size: 14px;
    color: #7A99B8;
    max-width: 580px;
    line-height: 1.7;
    margin-bottom: 28px;
}
.hero-stat-row { display: flex; gap: 32px; flex-wrap: wrap; }
.hero-stat { }
.hero-stat-num {
    font-family: 'DM Mono', monospace;
    font-size: 28px;
    font-weight: 500;
    color: #F7F8FA;
    line-height: 1;
}
.hero-stat-lbl {
    font-size: 11px;
    color: #4A6680;
    margin-top: 3px;
    letter-spacing: .04em;
}

/* ── Table ── */
.styled-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}
.styled-table th {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #7A8EA6;
    border-bottom: 1.5px solid #DDE2EA;
    padding: 8px 12px;
    text-align: left;
    font-weight: 500;
}
.styled-table td {
    padding: 9px 12px;
    border-bottom: 1px solid #F0F2F6;
    color: #2C3E50;
    vertical-align: top;
    line-height: 1.5;
}
.styled-table tr:hover td { background: #F7F8FA; }
.pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 2px;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: .04em;
}
.pill.high   { background: #E8F4FD; color: #0060B0; }
.pill.medium { background: #FEF6E8; color: #C4830A; }
.pill.low    { background: #FDECEE; color: #C0303B; }

/* ── Info callout ── */
.callout {
    background: #EEF6FF;
    border-left: 3px solid #0072CE;
    padding: 12px 16px;
    font-size: 12.5px;
    color: #1A3A5C;
    border-radius: 0 2px 2px 0;
    margin-top: 12px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)


# ─── DATA SETUP ─────────────────────────────────────────────────────────────
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
            'Risk_Auditing': {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':0},
            'Data_Privacy':  {'mandate':1,'activity_type':'active_soft','last_year':2024,'reach':0},
            'SME_Sandboxes': {'mandate':0,'activity_type':'active_soft','last_year':2024,'reach':0},
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
    
    # Actor metadata: location, group, city, Real Lat/Lon Coordinates
    actor_meta = {
        'Garante (DPA)':            {'group':'Government',   'city':'Rome',    'lat': 41.9028, 'lon': 12.4964, 'color':'#0072CE'},
        'AgID':                     {'group':'Government',   'city':'Rome',    'lat': 41.9200, 'lon': 12.5100, 'color':'#0072CE'},
        'CDP':                      {'group':'Government',   'city':'Rome',    'lat': 41.8800, 'lon': 12.4800, 'color':'#0072CE'},
        'Corte dei Conti':          {'group':'Government',   'city':'Rome',    'lat': 41.9100, 'lon': 12.4600, 'color':'#0072CE'},
        'Lombardy Region':          {'group':'Regional',     'city':'Milan',   'lat': 45.4642, 'lon': 9.1900,  'color':'#2ECC71'},
        'Confindustria Digitale':   {'group':'Industry',     'city':'Rome',    'lat': 41.8900, 'lon': 12.5200, 'color':'#F5A623'},
        'SME Networks (PMI)':       {'group':'Industry',     'city':'Bologna', 'lat': 44.4949, 'lon': 11.3426, 'color':'#F5A623'},
        'CDP Venture Capital':      {'group':'Industry',     'city':'Rome',    'lat': 41.8500, 'lon': 12.5000, 'color':'#F5A623'},
        'Altroconsumo':             {'group':'Civil Society','city':'Milan',   'lat': 45.4800, 'lon': 9.2000,  'color':'#E63946'},
        'Trade Unions (CGIL/CISL/UIL)':{'group':'Civil Society','city':'Rome', 'lat': 41.8700, 'lon': 12.4500, 'color':'#E63946'},
        'AIxIA':                    {'group':'Academia',     'city':'Turin',   'lat': 45.0703, 'lon': 7.6869,  'color':'#9B59B6'},
        'Fondazione Leonardo':      {'group':'Academia',     'city':'Rome',    'lat': 41.9300, 'lon': 12.4800, 'color':'#9B59B6'},
    }
    return data, weights, actor_meta

structured_data, ACTIVITY_WEIGHTS, ACTOR_META = load_data()
pillars = ['Risk_Auditing', 'Data_Privacy', 'SME_Sandboxes', 'Transparency', 'Funding_Grants']
pillar_labels = {
    'Risk_Auditing': 'Risk Auditing',
    'Data_Privacy': 'Data Privacy',
    'SME_Sandboxes': 'SME Sandboxes',
    'Transparency': 'Transparency',
    'Funding_Grants': 'Funding & Grants',
}
actors = list(structured_data.keys())

GROUP_COLORS = {
    'Government':   '#0072CE',
    'Regional':     '#2ECC71',
    'Industry':     '#F5A623',
    'Civil Society':'#E63946',
    'Academia':     '#9B59B6',
}

# ─── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 20px 0 10px;'>
        <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#0072CE;margin-bottom:6px;'>Intelligence Engine</div>
        <div style='font-size:16px;font-weight:700;color:#F7F8FA;line-height:1.3;margin-bottom:4px;'>Italy AI Governance</div>
        <div style='font-size:11px;color:#4A6680;margin-bottom:20px;'>2024–2026 National Strategy</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:#1E3048;margin-bottom:20px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.15em;color:#4A6680;text-transform:uppercase;margin-bottom:12px;'>Simulation Controls</div>", unsafe_allow_html=True)

    selected_pillar = st.selectbox(
        "STRATEGIC METRIC",
        options=pillars,
        format_func=lambda x: pillar_labels[x]
    )
    sim_year = st.slider("SIMULATION HORIZON", min_value=2023, max_value=2030, value=2026, step=1)
    decay_base = st.slider(
        "DORMANCY DECAY FACTOR", min_value=0.50, max_value=1.00, value=0.88, step=0.01,
        help="Policy obsolescence rate. At 0.88, dormant portfolios lose ~12% structural efficiency annually."
    )

    selected_group = st.multiselect(
        "FILTER BY ACTOR GROUP",
        options=list(GROUP_COLORS.keys()),
        default=list(GROUP_COLORS.keys()),
    )

    st.markdown("<div style='height:1px;background:#1E3048;margin:20px 0 16px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:11px;color:#4A6680;line-height:1.7;'>
    Scores combine statutory mandate, activity recency, and geographic reach. 
    Decay factor simulates institutional stagnation over time.
    </div>
    """, unsafe_allow_html=True)

# ─── COMPUTE ENGINE ─────────────────────────────────────────────────────────
def compute_scores(pillar, year, decay):
    scores = {}
    for actor in actors:
        cell = structured_data[actor][pillar]
        activity_w = ACTIVITY_WEIGHTS[cell['activity_type']]
        reach_bonus = 1 + cell['reach']
        raw = cell['mandate'] + activity_w * reach_bonus
        years_stale = max(0, year - cell['last_year'])
        scores[actor] = min(3.0, round(raw * (decay ** years_stale), 2))
    return scores

simulated_scores = compute_scores(selected_pillar, sim_year, decay_base)
filtered_actors = [a for a in actors if ACTOR_META[a]['group'] in selected_group]
s_series = pd.Series({a: simulated_scores[a] for a in filtered_actors}).sort_values(ascending=True)

full_heatmap_data = []
for actor in actors:
    row = {}
    for p in pillars:
        cell = structured_data[actor][p]
        raw = cell['mandate'] + ACTIVITY_WEIGHTS[cell['activity_type']] * (1 + cell['reach'])
        years_stale = max(0, sim_year - cell['last_year'])
        row[p] = min(3.0, round(raw * (decay_base ** years_stale), 2))
    full_heatmap_data.append(row)
df_heat = pd.DataFrame(full_heatmap_data, index=actors)

# ─── PAGES ──────────────────────────────────────────────────────────────────
page = st.sidebar.radio(
    "NAVIGATION",
    ["Briefing", "Stakeholder Map", "Capacity Matrix", "Decay Simulation", "Playbooks"],
    label_visibility="collapsed"
)

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 0 · BRIEFING (landing)
# ═══════════════════════════════════════════════════════════════════════════
if page == "Briefing":
    st.markdown("""
    <div class='hero-wrap'>
        <div class='hero-eyebrow'>Strategic Intelligence Report · Italy · AI Governance · 2024–2026</div>
        <div class='hero-title'>Where does <span>real</span> AI<br>governance power sit<br>in Italy?</div>
        <div class='hero-body'>
            This engine maps 12 institutional actors against 5 EU AI Act pillars,
            quantifies their structural decay over time, and surfaces the
            three highest-leverage intervention vectors for non-profit capital deployment.
        </div>
        <div class='hero-stat-row'>
            <div class='hero-stat'>
                <div class='hero-stat-num'>12</div>
                <div class='hero-stat-lbl'>Actors mapped</div>
            </div>
            <div class='hero-stat'>
                <div class='hero-stat-num'>5</div>
                <div class='hero-stat-lbl'>Governance pillars</div>
            </div>
            <div class='hero-stat'>
                <div class='hero-stat-num'>€44B</div>
                <div class='hero-stat-lbl'>PNRR tracked</div>
            </div>
            <div class='hero-stat'>
                <div class='hero-stat-num'>3</div>
                <div class='hero-stat-lbl'>Intervention vectors</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Context
    st.markdown("""
    <div class='section-rule'>
        <span class='label'>Country Context</span><div class='line'></div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.markdown("""
        <div style='font-size:14px;color:#2C3E50;line-height:1.85;'>
        Italy's AI governance landscape is structurally fragmented: enforcement authority is concentrated at the centre
        (Garante, Rome), while the industrial economy is dominated by SMEs that lack the compliance resources to engage
        with EU AI Act requirements. The PNRR injects €44B+ into digital transformation, but disbursement bodies operate
        with near-zero internal AI risk frameworks.
        <br><br>
        This creates three compounding gaps: <strong>regulatory-industrial distance</strong> (enforcement designed for large enterprises),
        <strong>Rome–region asymmetry</strong> (wealthy northern regions hold sandbox budgets untethered from national safety standards),
        and <strong>capital without conditionality</strong> (CDP deploys €30B+ with no AI safety due diligence requirements).
        </div>
        """, unsafe_allow_html=True)

    with c2:
        # Key facts as clean tiles
        facts = [
            ("99%", "of Italian businesses are SMEs (PMI)", "normal"),
            ("€13.4B", "available via Transizione 4.0 for SME digitisation", "normal"),
            ("0", "formal AI risk checkpoints in CDP investment criteria", "alert"),
            ("2023", "Italy became 1st EU country to ban an AI product (ChatGPT)", "normal"),
        ]
        for val, lbl, style in facts:
            color = "#E63946" if style == "alert" else "#0D1B2A"
            st.markdown(f"""
            <div style='background:#FFFFFF;border:1px solid #DDE2EA;border-radius:2px;
                        padding:14px 16px;margin-bottom:10px;'>
                <div style='font-family:DM Mono,monospace;font-size:22px;font-weight:500;color:{color};'>{val}</div>
                <div style='font-size:12px;color:#7A8EA6;margin-top:3px;'>{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    # Pillar overview table
    st.markdown("""
    <div class='section-rule'>
        <span class='label'>Governance Pillars</span><div class='line'></div>
    </div>
    """, unsafe_allow_html=True)

    pillar_info = [
        ("Risk Categorisation & Auditing", "EU AI Act Articles 6–51. Classification of AI systems by risk level and mandatory conformity assessment.", "High", "Garante, AgID, Corte dei Conti"),
        ("Data Privacy & Copyright", "GDPR enforcement + AI Act data governance provisions. Italy most active EU enforcer of AI/GDPR intersection.", "High", "Garante (dominant), Altroconsumo"),
        ("SME Innovation Sandboxes", "Art. 57 EU AI Act mandates member-state sandboxes. Italy has stated intent but zero funded operational implementation.", "Low", "Lombardy Region (de facto)"),
        ("System Transparency", "Art. 13–14 AI Act. Explainability obligations. Strong in theory; no audit tooling for Italian PMIs exists.", "Medium", "Trade Unions, Altroconsumo"),
        ("Funding & Grants", "PNRR M1C2 (€13.4B), M4C1 (€11.4B), M4C2 (€11.8B), CDP Venture (€500M). Access routes fragmented.", "High", "CDP, AgID, CDP Venture Capital"),
    ]

    html_rows = ""
    for name, desc, level, lead in pillar_info:
        pill_class = "high" if level == "High" else "medium" if level == "Medium" else "low"
        html_rows += f"""
        <tr>
            <td><strong>{name}</strong></td>
            <td>{desc}</td>
            <td><span class='pill {pill_class}'>{level}</span></td>
            <td style='font-size:11px;color:#0072CE;'>{lead}</td>
        </tr>"""

    st.markdown(f"""
    <table class='styled-table'>
        <thead><tr>
            <th style='width:20%'>Pillar</th>
            <th>Description</th>
            <th style='width:8%'>Activity</th>
            <th style='width:22%'>Lead Actor(s)</th>
        </tr></thead>
        <tbody>{html_rows}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # Critical gaps
    st.markdown("""
    <div class='section-rule'>
        <span class='label'>Critical Governance Gaps</span><div class='line'></div>
    </div>
    """, unsafe_allow_html=True)

    gaps = [
        ("G1", "#E63946", "SME Compliance Void",
         "Italy's 4.4M SMEs are the primary EU AI Act subjects but have no funded compliance support. "
         "Garante's enforcement posture (modelled on GDPR for large entities) creates regulatory exposure "
         "without practical pathways. The Transizione 4.0 tax credit funds AI adoption but includes no "
         "safety requirement — building AI risk in SMEs with zero AI governance."),
        ("G2", "#F5A623", "Capital Without Conditionality",
         "CDP controls €30B+ in deployment-stage capital (PNRR + Venture) with zero internal AI risk "
         "framework. Unlike the EIB (which has integrated AI ethics criteria since 2021), CDP applies "
         "no safety due diligence to AI investments. This is Italy's largest unmonitored AI pipeline."),
        ("G3", "#9B59B6", "Rome–Region Sandbox Disconnect",
         "Lombardy Region has the budget and political will to run AI sandboxes (highest score: 3.0), "
         "but operates entirely outside national safety frameworks set by Garante/AgID. Northern "
         "industrial AI pilots have no compliance bridge back to Rome's regulatory standards."),
    ]

    gcols = st.columns(3, gap="medium")
    for i, (code, color, title, body) in enumerate(gaps):
        with gcols[i]:
            st.markdown(f"""
            <div style='background:#FFFFFF;border:1px solid #DDE2EA;border-top:3px solid {color};
                        border-radius:2px;padding:20px;height:100%;'>
                <div style='font-family:DM Mono,monospace;font-size:10px;color:{color};
                            letter-spacing:.12em;margin-bottom:8px;'>{code} · GAP</div>
                <div style='font-size:14px;font-weight:700;color:#0D1B2A;margin-bottom:10px;'>{title}</div>
                <div style='font-size:12px;color:#4A5E75;line-height:1.7;'>{body}</div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1 · STAKEHOLDER MAP (Plotly Interactive)
# ═══════════════════════════════════════════════════════════════════════════
elif page == "Stakeholder Map":
    st.markdown("""
    <div style='padding:24px 0 8px;'>
        <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.15em;color:#7A8EA6;
                    text-transform:uppercase;margin-bottom:6px;'>Geospatial Intelligence</div>
        <div style='font-size:22px;font-weight:700;color:#0D1B2A;margin-bottom:4px;'>Italian AI Actor Map</div>
        <div style='font-size:13px;color:#7A8EA6;'>Interactive institutional geography of the AI governance ecosystem. 
        Power is concentrated in Rome; innovation capital clusters in the North.</div>
    </div>
    """, unsafe_allow_html=True)

    map_col, info_col = st.columns([3, 2], gap="large")

    with map_col:
        selected_actor_for_map = st.selectbox(
            "Highlight actor",
            options=["All"] + actors,
            index=0,
            label_visibility="collapsed"
        )

        # 1. Initialize Plotly Map Figure
        fig_map = go.Figure()

        # 2. Add each actor as a coordinate point
        for actor, meta in ACTOR_META.items():
            if meta['group'] not in selected_group:
                continue
            
            score = simulated_scores[actor]
            opacity = 1.0 if (selected_actor_for_map == "All" or selected_actor_for_map == actor) else 0.2
            
            # Draw the point
            fig_map.add_trace(go.Scattermapbox(
                lat=[meta['lat']],
                lon=[meta['lon']],
                mode='markers+text' if selected_actor_for_map == actor else 'markers',
                marker=go.scattermapbox.Marker(
                    size=10 + (score * 8),  # Radius scales cleanly with the score
                    color=meta['color'],
                    opacity=opacity,
                ),
                text=[f"{score:.1f}"] if selected_actor_for_map == actor else None,
                textfont=dict(size=14, color='black', family="Arial Black"),
                textposition="top right",
                hoverinfo='text',
                hovertext=f"<b>{actor}</b><br>Group: {meta['group']}<br>City: {meta['city']}<br>Score: <b>{score:.2f}</b>",
                name=actor,
                showlegend=False
            ))

        # 3. Configure the Professional Base Map (carto-positron)
        fig_map.update_layout(
            mapbox=dict(
                style="carto-positron",  # Professional, muted light-grey corporate map
                center=dict(lat=42.5, lon=12.5), # Centered on Italy
                zoom=4.8
            ),
            margin={"r":0,"t":0,"l":0,"b":0}, # Remove all padding
            height=550,
            paper_bgcolor="#F7F8FA"
        )

        # Render the interactive map
        st.plotly_chart(fig_map, use_container_width=True)

        # Custom Legend below the map
        legend_html = "<div class='pin-legend'>"
        for group, color in GROUP_COLORS.items():
            legend_html += f"""
            <div class='pin-item'>
                <div class='pin-dot' style='background:{color}'></div>
                {group}
            </div>"""
        legend_html += "</div>"
        st.markdown(legend_html, unsafe_allow_html=True)

    with info_col:
        st.markdown("""
        <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.12em;
                    text-transform:uppercase;color:#7A8EA6;margin-bottom:14px;'>Actor Directory</div>
        """, unsafe_allow_html=True)

        # Sort actors by score (highest to lowest) for the directory display
        sorted_actors = sorted([a for a in actors if ACTOR_META[a]['group'] in selected_group], 
                               key=lambda x: simulated_scores[x], reverse=True)

        for actor in sorted_actors:
            meta = ACTOR_META[actor]
            score = simulated_scores[actor]
            color = meta['color']
            bar_w = int((score / 3.0) * 100)
            
            # Grey out directory cards if they are not the currently selected actor
            card_opacity = "1.0" if (selected_actor_for_map == "All" or selected_actor_for_map == actor) else "0.3"
            
            st.markdown(f"""
            <div style='background:#FFFFFF;border:1px solid #DDE2EA;border-radius:2px;
                        padding:12px 14px;margin-bottom:8px; opacity:{card_opacity}; transition: opacity 0.3s;'>
                <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px;'>
                    <div>
                        <div style='font-size:12px;font-weight:600;color:#0D1B2A;'>{actor}</div>
                        <div style='font-size:10px;color:{color};font-family:DM Mono,monospace;
                                    letter-spacing:.06em;margin-top:2px;'>{meta["group"]} · {meta["city"]}</div>
                    </div>
                    <div style='font-family:DM Mono,monospace;font-size:16px;font-weight:500;
                                color:#0D1B2A;'>{score:.2f}</div>
                </div>
                <div style='height:3px;background:#F0F2F6;border-radius:2px;'>
                    <div style='height:3px;width:{bar_w}%;background:{color};border-radius:2px;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2 · CAPACITY MATRIX
# ═══════════════════════════════════════════════════════════════════════════
elif page == "Capacity Matrix":
    st.markdown("""
    <div style='padding:24px 0 16px;'>
        <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.15em;color:#7A8EA6;
                    text-transform:uppercase;margin-bottom:6px;'>Full Cross-Reference</div>
        <div style='font-size:22px;font-weight:700;color:#0D1B2A;'>Dynamic Capacity Matrix</div>
        <div style='font-size:13px;color:#7A8EA6;margin-top:4px;'>
            All actors × all pillars. Red dots mark priority non-profit intervention cells.
            Scores update with sidebar simulation parameters.
        </div>
    </div>
    """, unsafe_allow_html=True)

    fig2, ax2 = plt.subplots(figsize=(12, 7), facecolor='#FFFFFF')
    ax2.set_facecolor('#FFFFFF')

    prof_cmap = LinearSegmentedColormap.from_list(
        'intel_blue', ['#F7F8FA', '#B9D1EA', '#4A88C0', '#0C2C52'], N=256
    )

    filtered_heat = df_heat.loc[[a for a in actors if ACTOR_META[a]['group'] in selected_group]]

    sns.heatmap(
        filtered_heat,
        ax=ax2,
        cmap=prof_cmap,
        vmin=0, vmax=3,
        annot=True,
        fmt='.1f',
        annot_kws={'size': 11, 'weight': 'bold', 'color': '#0D1B2A'},
        linewidths=2.5,
        linecolor='#F7F8FA',
        cbar_kws={'shrink': 0.6, 'pad': 0.02},
    )

    ax2.xaxis.tick_top()
    ax2.xaxis.set_label_position('top')
    ax2.tick_params(left=False, top=False, bottom=False, length=0)

    clean_headers = [pillar_labels[p] for p in pillars]
    ax2.set_xticklabels(clean_headers, rotation=0, ha='center', fontsize=10,
                         fontweight='600', color='#333333', fontfamily='DejaVu Sans')
    ax2.set_yticklabels(filtered_heat.index, rotation=0, fontsize=10,
                         color='#333333', fontfamily='DejaVu Sans')

    # Intervention flags
    flag_actors = ['SME Networks (PMI)', 'CDP', 'Fondazione Leonardo', 'Lombardy Region']
    flag_pillars = [2, 0, 2, 2]
    for fa, fp in zip(flag_actors, flag_pillars):
        if fa in filtered_heat.index:
            r = list(filtered_heat.index).index(fa)
            ax2.plot(fp + 0.82, r + 0.18, marker='o', markersize=7,
                     color='#E63946', markeredgecolor='white', markeredgewidth=1.2, zorder=5)

    cbar = ax2.collections[0].colorbar
    cbar.ax.tick_params(labelsize=9)
    cbar.set_ticks([0, 1, 2, 3])
    cbar.set_ticklabels(['0 — Gap', '1 — Weak', '2 — Moderate', '3 — Strong'])

    plt.tight_layout(pad=1.5)
    st.pyplot(fig2)

    st.markdown(f"""
    <div class='callout'>
        <strong>Reading guide:</strong> Scores combine statutory mandate, activity type weight 
        (ongoing enforcement = 1.0 → expired = 0.1), and geographic reach, then decayed by 
        {(1-decay_base)*100:.0f}% per year of inactivity from the simulation horizon ({sim_year}). 
        Red dots mark cells where non-profit intervention can fill a structural gap with high leverage.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3 · DECAY SIMULATION
# ═══════════════════════════════════════════════════════════════════════════
elif page == "Decay Simulation":
    st.markdown(f"""
    <div style='padding:24px 0 8px;'>
        <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.15em;color:#7A8EA6;
                    text-transform:uppercase;margin-bottom:6px;'>Structural Decay Analysis</div>
        <div style='font-size:22px;font-weight:700;color:#0D1B2A;margin-bottom:4px;'>Capacity Delta Profile</div>
        <div style='font-size:13px;color:#7A8EA6;'>
            Simulated capacity in <strong>{sim_year}</strong> on <strong>{pillar_labels[selected_pillar]}</strong>,
            accounting for institutional stagnation since last active enforcement.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    tiles = [
        (k1, "Avg Portfolio Readiness", f"{s_series.mean():.2f} / 3.00", "Simulated system mean", "normal"),
        (k2, "Max Systemic Risk", s_series.index[0] if len(s_series) else "—", "Lowest capacity actor", "alert"),
        (k3, "Ecosystem Anchor", s_series.index[-1] if len(s_series) else "—", "Highest capacity actor", "normal"),
        (k4, "Actors Below 1.0", str(int((s_series < 1.0).sum())), "Structural gap count", "amber"),
    ]
    for col, label, val, sub, style in tiles:
        with col:
            st.markdown(f"""
            <div class='metric-tile {style}'>
                <div class='metric-label'>{label}</div>
                <div class='metric-value {"alert" if style=="alert" else ""}'>{val}</div>
                <div class='metric-sub'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    BG = '#1E293B'
    TEXT_PRIMARY = '#F8FAFC'
    TEXT_SEC = '#CBD5E1'
    BAR_NORMAL = '#38BDF8'
    BAR_ALERT  = '#FB7185'
    BAR_AMBER  = '#FBBF24'

    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    fig, ax = plt.subplots(figsize=(10, max(5, len(s_series) * 0.65 + 1)), facecolor=BG)
    ax.set_facecolor(BG)

    def bar_color(i, val):
        if i == 0: return BAR_ALERT
        if val < 1.0: return BAR_AMBER
        return BAR_NORMAL

    colors = [bar_color(i, v) for i, v in enumerate(s_series.values)]
    bars = ax.barh(s_series.index, s_series.values, color=colors, height=0.55)

    for bar, val in zip(bars, s_series.values):
        ax.text(val + 0.05, bar.get_y() + bar.get_height() / 2,
                f'{val:.2f}', va='center', fontweight='bold',
                color=bar.get_facecolor(), fontsize=10.5)

    # Threshold lines
    ax.axvline(1.0, color='#94A3B8', lw=1, ls='--', alpha=0.5, label='Weak threshold (1.0)')
    ax.axvline(2.0, color='#64748B', lw=1, ls=':', alpha=0.5, label='Moderate threshold (2.0)')

    ax.set_xlim(0, 3.5)
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(axis='both', length=0)
    ax.set_xticks([])
    ax.set_yticklabels(s_series.index, fontsize=10.5, fontweight='500', color=TEXT_SEC)
    ax.legend(loc='lower right', fontsize=9, framealpha=0,
              labelcolor=TEXT_SEC, facecolor=BG)

    fig.text(0.02, 0.97, f"Structural Decay Simulation: {pillar_labels[selected_pillar]}",
             fontsize=14, fontweight='bold', color=TEXT_PRIMARY, va='top')
    fig.text(0.02, 0.92,
             f"Simulated capacity in {sim_year} · Decay factor {decay_base:.2f} · "
             f"System mean: {s_series.mean():.2f}",
             fontsize=10, color=TEXT_SEC, va='top')

    plt.tight_layout(rect=[0, 0, 1, 0.88])
    st.pyplot(fig)

    st.markdown("""
    <div class='callout'>
        <strong>How to read this:</strong> Amber bars represent actors scoring below 1.0 — 
        structural gaps where mandate exists on paper but enforcement or activity has been absent 
        long enough to decay below functional threshold. These are the highest-priority targets 
        for non-profit capacity-building investment.
    </div>
    """, unsafe_allow_html=True)

    # Trajectory chart (multi-year)
    st.markdown("""
    <div class='section-rule'>
        <span class='label'>Decay Trajectories 2024–2030</span><div class='line'></div>
    </div>
    """, unsafe_allow_html=True)

    years = list(range(2024, 2031))
    fig3, ax3 = plt.subplots(figsize=(10, 4.5), facecolor='#FFFFFF')
    ax3.set_facecolor('#FFFFFF')

    top_actors = s_series.tail(5).index.tolist()[::-1]  # top 5
    traj_colors = ['#0072CE', '#E63946', '#F5A623', '#2ECC71', '#9B59B6']

    for actor, color in zip(top_actors, traj_colors):
        traj = []
        for y in years:
            cell = structured_data[actor][selected_pillar]
            raw = cell['mandate'] + ACTIVITY_WEIGHTS[cell['activity_type']] * (1 + cell['reach'])
            stale = max(0, y - cell['last_year'])
            traj.append(min(3.0, round(raw * (decay_base ** stale), 2)))
        ax3.plot(years, traj, color=color, lw=2, marker='o', markersize=5,
                 label=actor, markerfacecolor='white', markeredgewidth=1.5)

    ax3.axhline(1.0, color='#DDE2EA', lw=1, ls='--')
    ax3.set_xlim(2024, 2030)
    ax3.set_ylim(0, 3.2)
    ax3.set_ylabel('Simulated score', fontsize=10, color='#7A8EA6')
    ax3.set_xlabel('Year', fontsize=10, color='#7A8EA6')
    ax3.tick_params(colors='#9BAABF', length=0)
    ax3.spines[['top', 'right']].set_visible(False)
    ax3.spines[['bottom', 'left']].set_edgecolor('#DDE2EA')
    ax3.legend(fontsize=9, framealpha=0, loc='upper right')
    ax3.set_title(f'Top-5 actor trajectories · {pillar_labels[selected_pillar]}',
                  fontsize=11, color='#0D1B2A', fontweight='600', pad=10)

    plt.tight_layout()
    st.pyplot(fig3)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 4 · PLAYBOOKS
# ═══════════════════════════════════════════════════════════════════════════
elif page == "Playbooks":
    st.markdown("""
    <div style='padding:24px 0 8px;'>
        <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.15em;color:#7A8EA6;
                    text-transform:uppercase;margin-bottom:6px;'>Strategic Arbitrage</div>
        <div style='font-size:22px;font-weight:700;color:#0D1B2A;margin-bottom:4px;'>Capital Deployment Playbooks</div>
        <div style='font-size:13px;color:#7A8EA6;max-width:640px;'>
            Three targeted intervention vectors derived from the matrix cold spots.
            Each playbook specifies the leverage mechanism, the exact institutional target,
            and why generic alternatives fail in the Italian context.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. FIXED DICTIONARY: Replaced triple quotes with single-line strings
    playbooks = [
        {
            "num": "01",
            "badge": "RECOMMENDED",
            "badge_class": "go",
            "card_class": "",
            "score_ref": "SME Networks (PMI) × Transparency = 0.1 | Trade Unions × Transparency = 2.4",
            "title": "Force SME Algorithmic Transparency via National Labour Contracts",
            "vulnerability": "Italy's 4.4M SMEs run AI tools with zero transparency obligations in practice. Garante's enforcement is modelled on large-enterprise GDPR compliance. SMEs resist top-down regulatory mandates from Rome on cultural grounds — the <em>tessuto produttivo</em> (industrial fabric) of the North runs on trust networks, not compliance paperwork.",
            "vector": "Do not build open-source transparency toolkits and hope SMEs adopt them. Deploy grants to partner with <strong>Trade Unions (CGIL/CISL/UIL)</strong>, which hold a 2.4 score on System Transparency. By writing algorithmic explainability clauses directly into <strong>National Collective Labour Agreements (CCNL)</strong>, you force legally binding operational compliance via worker rights — a mechanism that already has enforcement infrastructure, bypasses corporate friction entirely, and is invisible to the lobbying counterpressure from Confindustria.",
            "entry": "CGIL Digital Rights desk (cgil.it/tematiche/digitale)",
            "timeline": "12–18 months for CCNL negotiation cycle",
            "budget_range": "€150K–400K (legal drafting + union partnership)",
        },
        {
            "num": "02",
            "badge": "RECOMMENDED",
            "badge_class": "go",
            "card_class": "",
            "score_ref": "CDP × Risk Auditing = 0.1 | CDP Venture Capital × SME Sandboxes = 2.1",
            "title": "Embed Safety Conditionality Inside the €30B CDP Funding Pipeline",
            "vulnerability": "CDP commands maximum capital deployment leverage (3.0 on Funding) but runs near-zero AI risk auditing capacity (0.1). Italy's promotional banking tradition — inherited from IRI-era state capitalism — prioritises deployment velocity over risk oversight. Unlike the EIB, which integrated AI ethics criteria in 2021, CDP applies no safety due diligence to AI investments. This creates an unmonitored €30B+ capital pipeline.",
            "vector": "Do not lobby Garante to impose restrictions on financial flows — that crosses institutional mandates and will be blocked. Instead, launch a <strong>capital-conditionality campaign</strong> targeting <strong>CDP Venture Capital</strong>, which already has a 2.1 score on SME Sandboxes — they are reform-adjacent. Design and advocate for mandatory 'AI Safety Due Diligence' criteria as a prerequisite for deep-tech portfolio entry. Model this on the EIB's AI Ethics Framework (2021) and propose it as a reputational upgrade ahead of Italy's 2026 G7 Presidency.",
            "entry": "CDP Venture Capital ESG working group + MEF strategic oversight desk",
            "timeline": "18–24 months (investment committee policy change)",
            "budget_range": "€80K–200K (policy research + advocacy coalition)",
        },
        {
            "num": "03",
            "badge": "COUNTER-RECOMMENDED",
            "badge_class": "stop",
            "card_class": "red",
            "score_ref": "Garante/AgID (Rome) vs Lombardy Region sandbox score = 3.0",
            "title": "Avoid Centralised Registries — Bridge the Rome–Region Divide Instead",
            "vulnerability": "Italy's constitutional architecture creates a structural trap: central regulators in Rome hold broad statutory AI oversight mandates but lack operational budget lines and SME reach, while wealthy northern regions (especially Lombardy) hold cash reserves and political will for AI sandboxes but operate completely outside national safety frameworks. Centralised registries proposed in Rome get ignored in Milan.",
            "vector": "Do not advocate for unified federal AI registries or central reporting mandates — these trigger constitutional gridlock (Art. 117 competency disputes) and are functionally ignored north of the Po valley. Instead, use capital to place <strong>civil society technologists as 'transparency embeds'</strong> inside Lombardy Region's active sandbox programme. This validates Rome's safety standards through regional execution power, creating an <em>implementation fait accompli</em> that central regulators can then formalise upward.",
            "entry": "Lombardy Region Innovation Unit",
            "timeline": "6–12 months to embed; 24 months to formalise",
            "budget_range": "€120K–300K (technologist embeds + documentation)",
        },
    ]

    # 2. FIXED HTML RENDERER: Single-line string to prevent markdown breaks
    for pb in playbooks:
        card_html = f"<div class='s-card {pb['card_class']}'><div style='display:flex;align-items:flex-start;gap:20px;'><div style='font-family:DM Mono,monospace;font-size:32px;font-weight:500;color:#DDE2EA;line-height:1;flex-shrink:0;'>{pb['num']}</div><div style='flex:1;'><div style='margin-bottom:8px;'><span class='badge {pb['badge_class']}'>{pb['badge']}</span><span style='font-family:DM Mono,monospace;font-size:10px;color:#9BAABF;margin-left:10px;'>{pb['score_ref']}</span></div><div style='font-size:16px;font-weight:700;color:#0D1B2A;margin-bottom:12px;'>{pb['title']}</div><div style='font-size:11px;font-family:DM Mono,monospace;letter-spacing:.08em;text-transform:uppercase;color:#7A8EA6;margin-bottom:4px;'>The Vulnerability</div><div style='font-size:13px;color:#4A5E75;line-height:1.7;margin-bottom:14px;'>{pb['vulnerability']}</div><div style='font-size:11px;font-family:DM Mono,monospace;letter-spacing:.08em;text-transform:uppercase;color:#7A8EA6;margin-bottom:4px;'>The Execution Vector</div><div style='font-size:13px;color:#2C3E50;line-height:1.7;margin-bottom:14px;'>{pb['vector']}</div><div style='display:flex;gap:24px;flex-wrap:wrap;border-top:1px solid #F0F2F6;padding-top:12px;'><div><div style='font-family:DM Mono,monospace;font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#9BAABF;margin-bottom:3px;'>Entry Point</div><div style='font-size:11px;color:#0072CE;'>{pb['entry']}</div></div><div><div style='font-family:DM Mono,monospace;font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#9BAABF;margin-bottom:3px;'>Timeline</div><div style='font-size:11px;color:#0D1B2A;'>{pb['timeline']}</div></div><div><div style='font-family:DM Mono,monospace;font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:#9BAABF;margin-bottom:3px;'>Indicative Budget</div><div style='font-size:11px;color:#0D1B2A;'>{pb['budget_range']}</div></div></div></div></div></div>"
        st.markdown(card_html, unsafe_allow_html=True)

    # 3. PNRR Funding Reference
    st.markdown("""
    <div class='section-rule'>
        <span class='label'>PNRR Funding Access Reference</span><div class='line'></div>
    </div>
    """, unsafe_allow_html=True)

    pnrr_rows = [
        ("M1C2 – Transizione 4.0", "€13.4B", "All Italian SMEs", "Tax credit 20–45% on AI capex", "mimit.gov.it/transizione40"),
        ("M4C1 – National Centres", "€11.4B", "Universities, research bodies, non-profits", "Competitive grants via MUR calls", "mur.gov.it/bandi"),
        ("M4C2 – R&D Partnerships", "€11.8B", "Companies in public-private consortia", "Matched R&D grants (30–50% co-fund)", "invitalia.it"),
        ("CDP Venture Capital", "€500M", "Italian AI scale-ups (Series A+)", "Direct equity / quasi-equity", "cdpventure.it"),
    ]

    rows_html = ""
    for stream, budget, eligible, instrument, portal in pnrr_rows:
        rows_html += f"<tr><td><strong>{stream}</strong></td><td style='font-family:DM Mono,monospace;color:#0072CE;'>{budget}</td><td>{eligible}</td><td>{instrument}</td><td><a href='https://{portal}' style='color:#0072CE;text-decoration:none;font-family:DM Mono,monospace;font-size:11px;'>{portal}</a></td></tr>"

    st.markdown(f"""
    <table class='styled-table'>
        <thead><tr>
            <th>Stream</th><th>Budget</th><th>Eligible</th>
            <th>Instrument</th><th>Portal</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """, unsafe_allow_html=True)
