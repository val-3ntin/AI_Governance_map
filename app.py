import sys
from pathlib import Path

# Allow `streamlit run app.py` without an editable install (Cloud + local).
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st
import pandas as pd
import numpy as np

from ai_gov_map.scoring import (
    ACTIVITY_WEIGHTS,
    GROUP_COLORS,
    PILLAR_LABELS,
    PILLARS,
    compute_heatmap,
    compute_scores,
    load_data,
)

# Heavy viz libs (matplotlib / seaborn / plotly) and the regulatory dashboard
# helpers are imported lazily inside the pages that need them so Streamlit
# Cloud can pass health checks before cold-importing those packages.


def _import_pyplot():
    """Lazy matplotlib.pyplot (no seaborn) for Decay Simulation charts."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _import_matplotlib():
    """Lazy matplotlib + seaborn for Capacity Matrix heatmap."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.colors import LinearSegmentedColormap

    return plt, sns, LinearSegmentedColormap


def _import_plotly_go():
    """Lazy plotly.graph_objects for Stakeholder Map."""
    import plotly.graph_objects as go

    return go

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Italy AI Governance Monitor",
    page_icon="◇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── GLOBAL CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --accent: #0072CE;
    --ink: #0D1B2A;
    --muted: #7A8EA6;
    --line: #DDE2EA;
    --bg: #F7F8FA;
}

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Sora', system-ui, sans-serif;
    color: var(--ink);
    background-color: var(--bg);
}
.stApp { background-color: var(--bg); }
.block-container { padding: 0 2rem 2.5rem 2rem; max-width: 1400px; }

/* ── Quiet global chrome ── */
.app-chrome {
    padding: 18px 0 14px;
    border-bottom: 1px solid var(--line);
    margin-bottom: 8px;
}
.app-chrome-name {
    font-size: 18px;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: -0.01em;
}
.app-chrome-prop {
    font-size: 13px;
    color: var(--muted);
    margin-top: 4px;
    max-width: 720px;
    line-height: 1.5;
}
.app-chrome-meta {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--accent);
    margin-top: 8px;
    letter-spacing: .04em;
}
.app-footer {
    margin-top: 36px;
    padding-top: 16px;
    border-top: 1px solid var(--line);
    font-size: 11px;
    color: var(--muted);
    line-height: 1.7;
}
.app-footer strong { color: #4A5E75; font-weight: 600; }

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
    border-bottom: 2px solid var(--accent) !important;
    background: transparent !important;
}

/* ── Metric tiles ── */
.metric-tile {
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-top: 3px solid var(--accent);
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
    border: 1px solid var(--line);
    border-left: 3px solid var(--accent);
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
.badge.go   { background: #E8F4FD; color: var(--accent); }
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
    color: var(--accent);
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
.hero-title span { color: var(--accent); }
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
    border-left: 3px solid var(--accent);
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
def _cached_load_data():
    return load_data()


@st.cache_data(show_spinner=False)
def _cached_last_refresh():
    from ai_gov_map.dashboard import format_refresh_label, last_fetched_at

    return format_refresh_label(last_fetched_at())


structured_data, _weights, ACTOR_META = _cached_load_data()
pillars = PILLARS
pillar_labels = PILLAR_LABELS
actors = list(structured_data.keys())
_refresh_label = _cached_last_refresh()

# Quiet global header (all pages)
st.markdown(
    f"""
    <div class='app-chrome'>
        <div class='app-chrome-name'>Italy AI Governance Monitor</div>
        <div class='app-chrome-prop'>
            Free EU/Italy AI regulation signals with capacity mapping and an auditable judgement layer.
        </div>
        <div class='app-chrome-meta'>Last data refresh · {_refresh_label}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 20px 0 10px;'>
        <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:#0072CE;margin-bottom:6px;'>Monitor</div>
        <div style='font-size:16px;font-weight:700;color:#F7F8FA;line-height:1.3;margin-bottom:4px;'>Italy AI Governance</div>
        <div style='font-size:11px;color:#4A6680;margin-bottom:20px;'>Regulatory feed · capacity map</div>
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

# ─── PAGES ──────────────────────────────────────────────────────────────────
page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Regulatory Feed",
        "Briefing",
        "Stakeholder Map",
        "Capacity Matrix",
        "Decay Simulation",
        "Playbooks",
    ],
    index=0,
    label_visibility="collapsed",
)

# Score / heatmap only for pages that render them (skip Briefing / Playbooks / Feed).
_SCORE_PAGES = {"Stakeholder Map", "Capacity Matrix", "Decay Simulation"}
simulated_scores = None
s_series = None
df_heat = None
if page in _SCORE_PAGES:
    simulated_scores = compute_scores(
        structured_data, selected_pillar, sim_year, decay_base
    )
    filtered_actors = [a for a in actors if ACTOR_META[a]["group"] in selected_group]
    s_series = pd.Series(
        {a: simulated_scores[a] for a in filtered_actors}
    ).sort_values(ascending=True)
    if page == "Capacity Matrix":
        df_heat = compute_heatmap(
            structured_data, sim_year, decay_base, pillars=pillars
        )

# ═══════════════════════════════════════════════════════════════════════════
# PAGE 0 · BRIEFING (landing)
# ═══════════════════════════════════════════════════════════════════════════
if page == "Briefing":
    st.markdown("""
    <div class='hero-wrap'>
        <div class='hero-eyebrow'>Strategic context · Italy · EU AI Act</div>
        <div class='hero-title'>Where does <span>real</span> AI<br>governance power sit<br>in Italy?</div>
        <div class='hero-body'>
            Maps 12 institutional actors against 5 EU AI Act pillars,
            quantifies structural decay over time, and surfaces
            high-leverage intervention vectors — alongside a live regulatory feed
            with human overrides.
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
    go = _import_plotly_go()
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
    from ai_gov_map.dashboard import build_heatmap_figure

    st.markdown("""
    <div style='padding:16px 0 12px;'>
        <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.15em;color:#7A8EA6;
                    text-transform:uppercase;margin-bottom:6px;'>Full Cross-Reference</div>
        <div style='font-size:22px;font-weight:700;color:#0D1B2A;'>Dynamic Capacity Matrix</div>
        <div style='font-size:13px;color:#7A8EA6;margin-top:4px;'>
            All actors × all pillars. Red markers flag priority intervention cells.
            Scores update with sidebar simulation parameters.
        </div>
    </div>
    """, unsafe_allow_html=True)

    filtered_heat = df_heat.loc[[a for a in actors if ACTOR_META[a]['group'] in selected_group]]
    flag_actors = ['SME Networks (PMI)', 'CDP', 'Fondazione Leonardo', 'Lombardy Region']
    flag_pillars = [2, 0, 2, 2]
    flag_cells = list(zip(flag_actors, flag_pillars))

    st.plotly_chart(
        build_heatmap_figure(filtered_heat, pillar_labels, flag_cells=flag_cells),
        use_container_width=True,
    )

    st.markdown(f"""
    <div class='callout'>
        <strong>Reading guide:</strong> Scores combine statutory mandate, activity type weight
        (ongoing enforcement = 1.0 → expired = 0.1), and geographic reach, then decayed by
        {(1-decay_base)*100:.0f}% per year of inactivity from the simulation horizon ({sim_year}).
        Red markers flag cells where non-profit intervention can fill a structural gap with high leverage.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3 · DECAY SIMULATION
# ═══════════════════════════════════════════════════════════════════════════
elif page == "Decay Simulation":
    from ai_gov_map.dashboard import build_decay_bar_figure

    plt = _import_pyplot()
    st.markdown(f"""
    <div style='padding:16px 0 8px;'>
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

    st.plotly_chart(
        build_decay_bar_figure(
            s_series,
            title=f"Structural Decay Simulation: {pillar_labels[selected_pillar]}",
            subtitle=(
                f"Simulated capacity in {sim_year} · Decay factor {decay_base:.2f} · "
                f"System mean: {s_series.mean():.2f}"
            ),
        ),
        use_container_width=True,
    )

    st.markdown("""
    <div class='callout'>
        <strong>How to read this:</strong> Amber bars represent actors scoring below 1.0 —
        structural gaps where mandate exists on paper but enforcement or activity has been absent
        long enough to decay below functional threshold. These are the highest-priority targets
        for non-profit capacity-building investment.
    </div>
    """, unsafe_allow_html=True)

    # Trajectory chart (multi-year) — keep Matplotlib for the line chart
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


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 5 · REGULATORY FEED (Phase 5 timeline + filters + export)
# ═══════════════════════════════════════════════════════════════════════════
elif page == "Regulatory Feed":
    from ai_gov_map.dashboard import (
        RISK_TIERS,
        build_monitor_frame,
        build_timeline_figure,
        dataframe_to_csv,
        dataframe_to_json,
        feed_display_frame,
        filter_monitor,
        list_tracked_entities,
        load_overrides_table,
    )

    st.markdown("""
    <div style='padding:12px 0 4px;'>
        <div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:.15em;color:#7A8EA6;
                    text-transform:uppercase;margin-bottom:6px;'>Compliance Monitor</div>
        <div style='font-size:22px;font-weight:700;color:#0D1B2A;margin-bottom:4px;'>Regulatory Feed</div>
        <div style='font-size:13px;color:#7A8EA6;max-width:720px;'>
            Timeline of ingested regulation items with effective risk tiers (summaries + human overrides),
            entity impact flags, and one-click export of the filtered view.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("How to read this", expanded=False):
        st.markdown(
            "Each row is a free-source regulation item. **Effective tier** is the human override "
            "when one exists, otherwise the auto summary tag (`unacceptable` / `high` / `limited` / "
            "`minimal`). **Needs review** flags low-confidence or heuristic tags; **Overridden** marks "
            "rows corrected in `overrides.json`. Filter by entity, tier, or text, then export the "
            "exact filtered view as CSV or JSON."
        )

    @st.cache_data(show_spinner=False)
    def _cached_monitor_frame():
        return build_monitor_frame()

    @st.cache_data(show_spinner=False)
    def _cached_entities():
        return list_tracked_entities()

    @st.cache_data(show_spinner=False)
    def _cached_overrides_table():
        return load_overrides_table()

    monitor_df = _cached_monitor_frame()
    tracked = _cached_entities()
    overrides_df = _cached_overrides_table()

    # Judgement strip — interview framing
    n_overrides = len(overrides_df)
    with st.expander(
        f"{n_overrides} human overrides — click to see why",
        expanded=False,
    ):
        st.caption(
            "Seeded disagreements for interview walkthrough — where offline/LLM tags were wrong. "
            "See README for narrative examples."
        )
        if overrides_df.empty:
            st.info("No overrides loaded.")
        else:
            st.dataframe(
                overrides_df[["id", "was_now", "reason"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.TextColumn("id", width="medium"),
                    "was_now": st.column_config.TextColumn("was → now", width="small"),
                    "reason": st.column_config.TextColumn("reason", width="large"),
                },
            )

    if monitor_df.empty:
        st.info(
            "No regulation data loaded. Run ingest to populate "
            "`data/regulation_data.csv`, or check that the file exists."
        )
    else:
        entity_options = {e["id"]: e["display_name"] for e in tracked}
        entity_ids = list(entity_options.keys())

        c1, c2, c3 = st.columns([1.2, 1, 1.4])
        with c1:
            selected_entities = st.multiselect(
                "Tracked entities",
                options=entity_ids,
                default=[],
                format_func=lambda eid: entity_options.get(eid, eid),
                help="Show items that match any selected entity (from entities.yaml / impact_flags).",
            )
        with c2:
            selected_tiers = st.multiselect(
                "Risk tiers",
                options=list(RISK_TIERS),
                default=list(RISK_TIERS),
                help="Filter on effective risk tier (override wins over summary).",
            )
        with c3:
            search_q = st.text_input(
                "Search title / excerpt",
                value="",
                placeholder="e.g. AI Act, AgID, biometric…",
            )

        with st.spinner("Updating feed…"):
            filtered = filter_monitor(
                monitor_df,
                entity_ids=selected_entities or None,
                risk_tiers=selected_tiers if selected_tiers else None,
                query=search_q or None,
            )

            n_total = len(monitor_df)
            n_show = len(filtered)
            review_n = (
                int(filtered["needs_review"].sum())
                if n_show and "needs_review" in filtered.columns
                else 0
            )
            overridden_n = (
                int(filtered["overridden"].sum())
                if n_show and "overridden" in filtered.columns
                else 0
            )

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Showing", f"{n_show} / {n_total}")
            m2.metric("Needs review", review_n)
            m3.metric("Overridden", overridden_n)
            m4.metric(
                "High / unacceptable",
                int(filtered["effective_tier"].isin(["high", "unacceptable"]).sum())
                if n_show
                else 0,
            )
            m5.metric("Sources", filtered["source"].nunique() if n_show else 0)

            st.plotly_chart(build_timeline_figure(filtered), use_container_width=True)

            if filtered.empty:
                st.warning("No matches — clear filters")
            else:
                # Intersection only — never KeyError if a badge col is missing.
                display_df = feed_display_frame(filtered)
                col_config = {
                    "url": st.column_config.LinkColumn("url", width="medium"),
                    "title": st.column_config.TextColumn("title", width="large"),
                    "effective_tier": st.column_config.TextColumn(
                        "effective_tier", width="small"
                    ),
                    "needs_review": st.column_config.CheckboxColumn("needs_review"),
                    "overridden": st.column_config.CheckboxColumn("overridden"),
                }
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    height=420,
                    column_config={
                        k: v for k, v in col_config.items() if k in display_df.columns
                    },
                )

            csv_bytes = dataframe_to_csv(filtered).encode("utf-8")
            json_bytes = dataframe_to_json(filtered).encode("utf-8")
            d1, d2, _ = st.columns([1, 1, 2])
            with d1:
                st.download_button(
                    "Download CSV",
                    data=csv_bytes,
                    file_name="regulatory_feed_filtered.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with d2:
                st.download_button(
                    "Download JSON",
                    data=json_bytes,
                    file_name="regulatory_feed_filtered.json",
                    mime="application/json",
                    use_container_width=True,
                )

# ─── FOOTER (all pages) ─────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class='app-footer'>
        <strong>Sources</strong> · EUR-Lex · OECD.AI (curated) · AgID / Garante RSS · GDELT
        &nbsp;·&nbsp; <strong>Last ingest</strong> · {_refresh_label}
        &nbsp;·&nbsp; Not legal advice — research / portfolio demo only.
    </div>
    """,
    unsafe_allow_html=True,
)
