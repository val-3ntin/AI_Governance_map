with tab1:
    clean_pillar_name = selected_pillar.replace('_', ' ')
    
    # ─── PREMIUM SOFT DARK THEME ───────────────────────────────────────────
    bg_color = '#1E293B'           # Deep Slate/Navy (Much softer than pure black)
    text_primary = '#F8FAFC'       # Crisp Off-White for main titles
    text_secondary = '#CBD5E1'     # Lighter, highly readable silver/grey for subtitles
    bar_normal = '#38BDF8'         # Bright Sky Blue (Elegant and luminous)
    bar_alert = '#FB7185'          # Soft Rose/Coral for the vulnerability alert
    
    # Render Matplotlib Figure
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    fig, ax = plt.subplots(figsize=(10, 6.5), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    # Assign colors: Red for the lowest score, Blue for the rest
    colors = [bar_alert if i == 0 else bar_normal for i in range(len(s_series))]
    bars = ax.barh(s_series.index, s_series.values, color=colors, height=0.55)

    # Direct Labeling on the bars
    for bar, val in zip(bars, s_series.values):
        ax.text(val + 0.04, bar.get_y() + bar.get_height() / 2, 
                f'{val:.2f}', va='center', fontweight='bold', 
                color=bar.get_facecolor(), fontsize=10.5)
        
    ax.set_xlim(0, 3.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', length=0)
    ax.set_xticks([])
    
    # Set y-axis labels to the readable silver
    ax.set_yticklabels(s_series.index, fontsize=10.5, fontweight='500', color=text_secondary)

    # Add insight titles with excellent contrast
    fig.text(0.02, 0.94, f"Structural Decay Simulation: {clean_pillar_name}", 
             fontsize=15, fontweight='bold', color=text_primary)
    fig.text(0.02, 0.88, f"Simulated systemic capacity in {sim_year} accounting for historical performance stagnation.", 
             fontsize=11, color=text_secondary)

    # THE FIX: Restrict tight_layout to the bottom 85% of the figure so titles don't overlap
    plt.tight_layout(rect=[0, 0, 1, 0.85])
    st.pyplot(fig)
    
    st.info("**Strategic Insight:** Notice how 'On-Paper' mandates from 2021/2022 quickly drag an actor to the bottom of the rankings if no active enforcement has occurred recently.")        text-transform: uppercase;
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
""", unsafe_allow_html=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("<p style='color: #002B49; font-size: 28px; font-weight: 700; margin-bottom: 5px;'>Italy AI Governance: Strategic Decision Engine</p>", unsafe_allow_html=True)
st.markdown("<p style='color: #555555; font-size: 14px; margin-bottom: 25px;'>Stress-testing public administration adoption, regulatory latency, and institutional structural drivers under the 2024-2026 National Strategy.</p>", unsafe_allow_html=True)

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
    st.markdown("<p style='font-size: 18px; font-weight: 700; color: #002B49; margin-bottom: 5px;'>Simulation Controls</p>", unsafe_allow_html=True)
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
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
        <div class='kpi-card alert'>
            <div class='kpi-title'>Maximum Systemic Risk</div>
            <div class='kpi-value alert'>{s_series.index[0]}</div>
            <div class='kpi-subtitle'>Lowest metric output capacity</div>
        </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-title'>Ecosystem Anchor Partner</div>
            <div class='kpi-value'>{s_series.index[-1]}</div>
            <div class='kpi-subtitle'>Highest functional capacity cell</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── ANALYTICAL WORKSPACES ───────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Capacity Delta Profile", "🏁 Matrix Analytics", "♟️ Strategic Playbooks"])

with tab1:
    clean_pillar_name = selected_pillar.replace('_', ' ')
    
    # ─── DARK THEME COLOR PALETTE ──────────────────────────────────────────
    bg_color = '#121212'           # Deep charcoal/black background
    text_primary = '#FFFFFF'       # Pure white for main titles
    text_secondary = '#A0A0A0'     # Soft grey for subtitles and axis labels
    bar_normal = '#3A86FF'         # Vibrant corporate blue (pops on dark bg)
    bar_alert = '#E63946'          # High-contrast red for the vulnerability
    
    # Render Matplotlib Figure
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    fig, ax = plt.subplots(figsize=(10, 6.5), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    # Assign colors: Red for the lowest score, Blue for the rest
    colors = [bar_alert if i == 0 else bar_normal for i in range(len(s_series))]
    bars = ax.barh(s_series.index, s_series.values, color=colors, height=0.55)

    # Direct Labeling on the bars
    for bar, val in zip(bars, s_series.values):
        ax.text(val + 0.04, bar.get_y() + bar.get_height() / 2, 
                f'{val:.2f}', va='center', fontweight='bold', 
                color=bar.get_facecolor(), fontsize=10.5)
        
    ax.set_xlim(0, 3.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', length=0)
    ax.set_xticks([])
    
    # Set y-axis labels to soft grey
    ax.set_yticklabels(s_series.index, fontsize=10.5, fontweight='500', color=text_secondary)

    # Add insight titles with white/grey contrast
    fig.text(0.02, 0.94, f"Structural Decay Simulation: {clean_pillar_name}", 
             fontsize=15, fontweight='bold', color=text_primary)
    fig.text(0.02, 0.88, f"Simulated systemic capacity in {sim_year} accounting for historical performance stagnation.", 
             fontsize=11, color=text_secondary)

    # THE FIX: Restrict tight_layout to the bottom 85% of the figure so titles don't overlap
    plt.tight_layout(rect=[0, 0, 1, 0.85])
    st.pyplot(fig)
    
    st.info("**Strategic Insight:** Notice how 'On-Paper' mandates from 2021/2022 quickly drag an actor to the bottom of the rankings if no active enforcement has occurred recently.")
    
with tab2:
    st.markdown("<p style='font-size: 16px; font-weight: 700; color: #111111;'>Dynamic Matrix Cross-Reference</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 13px; color: #555555;'>This system architecture matrix updates dynamically as simulation parameters shift. Red indicators represent prioritized non-profit intervention fields.</p>", unsafe_allow_html=True)
    
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

    # 3. Clean up the Axes
    ax2.xaxis.tick_top()
    ax2.xaxis.set_label_position('top')
    ax2.tick_params(left=False, top=False, bottom=False)

    clean_headers = [p.replace('_', ' ') for p in pillars]
    ax2.set_xticklabels(clean_headers, rotation=0, ha='center', fontsize=10, fontweight='bold', color='#333333')
    ax2.set_yticklabels(df_heat.index, rotation=0, fontsize=10.5, fontweight='500', color='#333333')

    # 4. Add the Intervention Opportunity Flags
    flags = [(6, 2), (2, 0), (6, 3), (11, 2), (8, 2), (4, 3)]
    for (y, x) in flags:
        ax2.plot(x + 0.85, y + 0.15, marker='o', markersize=8, color='#E63946', markeredgecolor='white')

    plt.tight_layout()
    st.pyplot(fig2)
    
with tab3:
    st.markdown("<p style='font-size: 16px; font-weight: 700; color: #111111;'>Strategic Arbitrage & Capital Deployment Playbooks</p>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 13.5px; color: #555555;'>Cross-referencing legal mandates against structural funding pipelines isolates three key intervention vectors. Philanthropic grants should bypass standard regulatory lobbying and align with these operational levers.</p>", unsafe_allow_html=True)
    st.divider()

    # ─── PLAYBOOK 1 ──────────────────────────────────────────────────────────
    st.markdown("""
        <div class='strategy-card'>
            <div class='badge-do'>RECOMMENDED STRATEGY</div>
            <p style='font-size: 15px; font-weight: 700; color: #002B49; margin-top:5px; margin-bottom:5px;'>1. Force SME Algorithmic Transparency via National Labor Contracts</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Vulnerability:</b> While SME Networks (PMI) maintain non-existent transparency and sandbox scores (0.1), Italy's business infrastructure relies natively on high-trust informal local networks, heavily resisting top-down regulatory reporting dictates from Rome.</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Execution Vector:</b> Do not build open-source transparency toolkits for business entities. Instead, deploy grants to partner with major <b>Trade Unions (CGIL/CISL/UIL)</b>. Unions hold a robust 2.4 capacity on System Transparency. By writing algorithmic explainability mandates directly into National Collective Labor Agreements (CCNL), non-profits force legally binding operational compliance via established worker rights, entirely bypassing corporate friction.</p>
        </div>
    """, unsafe_allow_html=True)

    # ─── PLAYBOOK 2 ──────────────────────────────────────────────────────────
    st.markdown("""
        <div class='strategy-card'>
            <div class='badge-do'>RECOMMENDED STRATEGY</div>
            <p style='font-size: 15px; font-weight: 700; color: #002B49; margin-top:5px; margin-bottom:5px;'>2. Embed Safety Conditionality inside the €30B CDP Funding Pipeline</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Vulnerability:</b> Cassa Depositi e Prestiti (CDP) commands maximum capital deployment leverage (3.0) but runs a near-zero internal AI risk auditing capability (0.1). Italy's promotional banking tradition prioritizes macroeconomic transition speed over risk oversight, creating an unmonitored capital pipeline.</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Execution Vector:</b> Do not lobby the national data protection authority to curb financial lines. Instead, launch a capital-conditionality campaign targeting <b>CDP Venture Capital</b>. Because they maintain an active 2.1 footprint in SME Innovation Sandboxes, philanthropists can design and lobby for mandatory 'AI Safety Due Diligence' criteria, embedding compliance parameters directly into the deployment terms of deep-tech venture funds.</p>
        </div>
    """, unsafe_allow_html=True)

    # ─── PLAYBOOK 3 ──────────────────────────────────────────────────────────
    st.markdown("""
        <div class='strategy-card'>
            <div class='badge-not'>COUNTER-RECOMMENDED LOBBYING</div>
            <p style='font-size: 15px; font-weight: 700; color: #E63946; margin-top:5px; margin-bottom:5px;'>3. Avoid Centralized Registries — Bridge the Rome-Regional Divide Instead</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Structural Trap:</b> Italy's constitutional architecture creates a deep disconnect: central regulators in Rome (Garante, AgID) possess broad statutory oversight mandates but lack operational budget lines, while wealthy northern regions (Lombardy Region, scoring 3.0 on sandboxes) hold cash reserves but operate completely untethered from centralized safety frameworks.</p>
            <p style='font-size: 13.5px; color: #333333;'><b>The Execution Vector:</b> Do not advocate for centralized registries or unified federal mandates; these initiatives trigger constitutional gridlock and are functionally ignored. Instead, use capital to place civil society technologists as 'transparency embeds' inside active regional sandbox hubs, validating Rome's standards through regional execution power.</p>
        </div>
    """, unsafe_allow_html=True)
