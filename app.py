"""
Streamlit UI for the NC alimony + child-support model.

Run:
    .venv/bin/streamlit run app.py
"""

import streamlit as st
import pandas as pd
import altair as alt

from nc_alimony import (
    model,
    net_income,
    federal_tax_2025_single,
    nc_tax_2025,
    fica_2025,
    bcso_lookup,
    W_BASE,
    DEPENDENCY_GATE_RATIO,
)


st.set_page_config(
    page_title="NC Alimony Model",
    page_icon="⚖",
    layout="wide",
)

st.markdown(
    """
    <style>
      .metric-big { font-size: 2.4rem; font-weight: 700; }
      .metric-label { color: #888; font-size: 0.85rem; text-transform: uppercase; letter-spacing: .05em; }
      .gate-pill { display: inline-block; padding: 4px 10px; border-radius: 12px; background: #fff3cd; color: #663c00; font-size: 0.85rem; }
      .gate-pill.none { background: #d1f0d6; color: #1e5631; }
      .direction-pill { display:inline-block; padding:3px 8px; border-radius:8px; background:#eef; font-size:.8rem; color:#225; margin-left:.5rem;}
      .small-muted { color: #888; font-size: 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("North Carolina alimony + child-support calculator")
st.caption(
    "Tax year 2025 · single filers post-divorce · post-TCJA (alimony non-deductible) · NC Worksheet B for shared custody"
)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Inputs")

    G_p = st.number_input(
        "Payor gross annual income ($)",
        min_value=0, max_value=5_000_000, value=285_000, step=5_000,
    )
    G_a = st.number_input(
        "Party A gross annual income ($)",
        min_value=0, max_value=5_000_000, value=15_600, step=1_000,
        help="Default $15,600 ≈ federal minimum wage at 40 hrs/wk × 52 weeks.",
    )
    n_kids = st.number_input(
        "Number of joint children", min_value=0, max_value=8, value=2, step=1,
    )

    st.subheader("Custody")
    overnights_p = st.slider(
        "Payor overnights per year (Party A gets the rest)",
        min_value=0, max_value=365, value=183,
        help="≥123 for both parents qualifies as Worksheet B (shared custody). "
             "Anchor uses 183 (50/50).",
    )
    overnights_a = 365 - overnights_p

    st.subheader("Add-ons (monthly $)")
    health_ins = st.number_input(
        "Children's health insurance (paid by payor)", min_value=0, value=482, step=10,
        help="Per parties' agreement, payor pays health insurance in full. "
             "This flows into Worksheet B as an add-on the payor paid directly.",
    )
    child_care = st.number_input("Work-related child care", min_value=0, value=0, step=50)
    # Payor pays health insurance in full (parties' agreement); child care defaults to
    # the Worksheet B income-share split (neither side specially credited).
    addons_paid_p = health_ins
    direct_offset_p = 0.0

    bar_alimony = False
    mandate_alimony = False

    with st.expander("Advanced calibration"):
        w_payor = st.slider(
            "Payor weight w (calibrated 0.545 to anchor)",
            min_value=0.45, max_value=0.65, value=W_BASE, step=0.005,
        )

# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------
result = model(
    G_p, G_a, n_kids,
    overnights_p=overnights_p, overnights_a=overnights_a,
    bar_alimony=bar_alimony, mandate_alimony=mandate_alimony,
    health_ins=health_ins, child_care=child_care,
    addons_paid_p=addons_paid_p,
    direct_offset_p=direct_offset_p,
    w_payor=w_payor,
)

A_mo = result['A_monthly']
CS_mo = result['cs_monthly']
direction = result['cs_direction']
TH_p = result['take_home_p_monthly']
TH_a = result['take_home_a_monthly']
gate_fired = result.get('gate_fired')

# Identify CS flow direction for display
cs_arrow = " (P→A)" if direction == 'P_to_A' else " (A→P)" if direction == 'A_to_P' else ""

# ---------------------------------------------------------------------------
# Headline metrics
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="metric-label">Alimony (P → A)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-big">${A_mo:,.0f}/mo</div>', unsafe_allow_html=True)
    st.caption(f"${A_mo*12:,.0f}/yr")
with c2:
    st.markdown(f'<div class="metric-label">Child support{cs_arrow}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-big">${CS_mo:,.0f}/mo</div>', unsafe_allow_html=True)
    st.caption(f"${CS_mo*12:,.0f}/yr")
with c3:
    st.markdown('<div class="metric-label">Payor take-home</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-big">${TH_p:,.0f}/mo</div>', unsafe_allow_html=True)
    st.caption(f"After tax, alimony, CS")
with c4:
    st.markdown('<div class="metric-label">Party A take-home</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-big">${TH_a:,.0f}/mo</div>', unsafe_allow_html=True)
    margin = TH_p - TH_a
    if margin >= 0:
        st.caption(f"Payor leads by ${margin:,.0f}/mo (no-cross ✓)")
    else:
        st.caption(f"⚠ Party A leads by ${-margin:,.0f}/mo")

# ---------------------------------------------------------------------------
# Gate / status
# ---------------------------------------------------------------------------
if gate_fired:
    label_map = {
        'statutory_bar':    "Statutory bar (NCGS 50-16.3A(a))",
        'dependency_40pct_net': f"Dependency gate (Party A's net income ≥{DEPENDENCY_GATE_RATIO*100:.0f}% of combined net — not 'dependent' under NCGS 50-16.1A)",
        'de_minimis':       "De-minimis floor (income gap < $1,500/mo)",
    }
    st.markdown(
        f'<div class="gate-pill">⚠ Gate fired — alimony zeroed: <b>{label_map.get(gate_fired, gate_fired)}</b></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="gate-pill none">✓ No gate fired — interior alimony computed</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Detailed split table
# ---------------------------------------------------------------------------
st.subheader("Side-by-side cash flow")

N_p = result['N_p_annual']
N_a = result['N_a_annual']

# Per-side detail
fed_p = federal_tax_2025_single(G_p)
nc_p  = nc_tax_2025(G_p)
fica_p = fica_2025(G_p)
fed_a = federal_tax_2025_single(G_a)
nc_a  = nc_tax_2025(G_a)
fica_a = fica_2025(G_a)

cs_p_signed = CS_mo if direction == 'P_to_A' else (-CS_mo if direction == 'A_to_P' else 0.0)

rows = [
    ("Gross income (annual)",    f"${G_p:,.0f}",        f"${G_a:,.0f}"),
    ("Gross income (monthly)",   f"${G_p/12:,.0f}",     f"${G_a/12:,.0f}"),
    ("— Federal tax",            f"−${fed_p:,.0f}",     f"−${fed_a:,.0f}"),
    ("— NC state tax (4.25%)",   f"−${nc_p:,.0f}",      f"−${nc_a:,.0f}"),
    ("— FICA",                   f"−${fica_p:,.0f}",    f"−${fica_a:,.0f}"),
    ("Net income (annual)",      f"${N_p:,.0f}",        f"${N_a:,.0f}"),
    ("Net income (monthly)",     f"${N_p/12:,.0f}",     f"${N_a/12:,.0f}"),
    ("— Alimony paid",           f"−${A_mo:,.0f}/mo",   f"+${A_mo:,.0f}/mo"),
    ("— Child support",          (f"−${CS_mo:,.0f}/mo" if direction=='P_to_A' else (f"+${CS_mo:,.0f}/mo" if direction=='A_to_P' else "$0/mo")),
                                 (f"+${CS_mo:,.0f}/mo" if direction=='P_to_A' else (f"−${CS_mo:,.0f}/mo" if direction=='A_to_P' else "$0/mo"))),
    ("**Take-home (monthly)**",  f"**${TH_p:,.0f}**",   f"**${TH_a:,.0f}**"),
    ("**Take-home (annual)**",   f"**${TH_p*12:,.0f}**", f"**${TH_a*12:,.0f}**"),
]
df = pd.DataFrame(rows, columns=["Line", "Payor", "Party A"])
st.table(df)

# ---------------------------------------------------------------------------
# Worksheet B detail
# ---------------------------------------------------------------------------
with st.expander("Child Support Worksheet B detail"):
    if n_kids > 0:
        combined_mo = (G_p + G_a) / 12.0
        bcso = bcso_lookup(combined_mo, n_kids)
        bp = 1.5 * bcso
        s_p = (G_p / (G_p + G_a)) if (G_p + G_a) > 0 else 0.0
        s_a = 1.0 - s_p
        t_p = overnights_p / 365.0
        t_a = overnights_a / 365.0
        share_p = s_p * bp * t_a
        share_a = s_a * bp * t_p

        ws_rows = [
            ("Combined adjusted gross monthly", f"${combined_mo:,.0f}"),
            (f"BCSO ({n_kids} kid{'s' if n_kids != 1 else ''}, schedule)", f"${bcso:,.0f}"),
            ("× 1.5 shared-custody multiplier", f"${bp:,.0f}"),
            ("Payor income share s_p", f"{s_p:.1%}"),
            ("Party A income share s_a", f"{s_a:.1%}"),
            ("Payor overnight share t_p", f"{t_p:.1%}"),
            ("Party A overnight share t_a", f"{t_a:.1%}"),
            ("Payor's share of B′ × t_a", f"${share_p:,.0f}"),
            ("Party A's share of B′ × t_p", f"${share_a:,.0f}"),
            ("Direct offset to payor", f"${direct_offset_p:,.0f}"),
            ("**Net CS owed**", f"**${CS_mo:,.0f}/mo {direction.replace('_', ' → ')}**"),
        ]
        ws_df = pd.DataFrame(ws_rows, columns=["Worksheet B line", "Value"])
        st.table(ws_df)
    else:
        st.write("No children → no child support computed.")

# ---------------------------------------------------------------------------
# Sweep charts
# ---------------------------------------------------------------------------
st.subheader("Sensitivity")

tab1, tab2 = st.tabs(["Vary Party A's earnings (work incentive)", "Vary payor's earnings (no-cross)"])

with tab1:
    # Sweep G_a from 0 to max(200K, current+100K)
    g_a_max = max(200_000, G_a + 100_000)
    pts = list(range(0, int(g_a_max) + 1, 5_000))
    sweep_a_rows = []
    for g_a_test in pts:
        r = model(
            G_p, g_a_test, n_kids,
            overnights_p=overnights_p, overnights_a=overnights_a,
                    bar_alimony=bar_alimony, mandate_alimony=mandate_alimony,
            health_ins=health_ins, child_care=child_care,
            addons_paid_p=addons_paid_p,
            direct_offset_p=direct_offset_p,
            w_payor=w_payor,
        )
        sweep_a_rows.append({
            'Party A gross ($/yr)': g_a_test,
            'Alimony ($/mo)':       r['A_monthly'],
            'Child support ($/mo)': r['cs_monthly'] if r['cs_direction'] == 'P_to_A' else -r['cs_monthly'] if r['cs_direction'] == 'A_to_P' else 0,
            'Payor take-home ($/mo)':   r['take_home_p_monthly'],
            'Party A take-home ($/mo)': r['take_home_a_monthly'],
        })
    df_a = pd.DataFrame(sweep_a_rows)
    long_a = df_a.melt(id_vars=['Party A gross ($/yr)'], var_name='Series', value_name='$/mo')
    chart_a = alt.Chart(long_a).mark_line(point=False).encode(
        x=alt.X('Party A gross ($/yr):Q', axis=alt.Axis(format='$,.0f')),
        y=alt.Y('$/mo:Q', axis=alt.Axis(format='$,.0f')),
        color='Series:N',
        tooltip=['Series', alt.Tooltip('Party A gross ($/yr):Q', format='$,.0f'),
                 alt.Tooltip('$/mo:Q', format='$,.0f')],
    ).properties(height=380)
    # Mark current G_a
    rule = alt.Chart(pd.DataFrame({'x': [G_a]})).mark_rule(color='#888', strokeDash=[4,4]).encode(x='x:Q')
    st.altair_chart(chart_a + rule, use_container_width=True)
    st.caption(
        "Verifies user constraint #4 (work incentive): Party A's take-home should "
        "rise monotonically with her own earnings, and alimony should taper smoothly "
        "(no cliffs) as it phases out. Vertical dashed line marks current G_a."
    )

with tab2:
    g_p_max = max(1_000_000, G_p + 200_000)
    pts = [0, 25_000, 50_000, 75_000, 100_000, 150_000, 200_000, 250_000, 285_000,
           350_000, 500_000, 750_000, 1_000_000]
    pts = sorted(set([p for p in pts if p <= g_p_max] + [G_p]))
    sweep_p_rows = []
    for g_p_test in pts:
        r = model(
            g_p_test, G_a, n_kids,
            overnights_p=overnights_p, overnights_a=overnights_a,
                    bar_alimony=bar_alimony, mandate_alimony=mandate_alimony,
            health_ins=health_ins, child_care=child_care,
            addons_paid_p=addons_paid_p,
            direct_offset_p=direct_offset_p,
            w_payor=w_payor,
        )
        sweep_p_rows.append({
            'Payor gross ($/yr)': g_p_test,
            'Alimony ($/mo)':     r['A_monthly'],
            'Payor take-home ($/mo)':   r['take_home_p_monthly'],
            'Party A take-home ($/mo)': r['take_home_a_monthly'],
            'No-cross margin ($/mo)':   r['take_home_p_monthly'] - r['take_home_a_monthly'],
        })
    df_p = pd.DataFrame(sweep_p_rows)
    long_p = df_p.melt(id_vars=['Payor gross ($/yr)'], var_name='Series', value_name='$/mo')
    chart_p = alt.Chart(long_p).mark_line(point=True).encode(
        x=alt.X('Payor gross ($/yr):Q', axis=alt.Axis(format='$,.0f')),
        y=alt.Y('$/mo:Q', axis=alt.Axis(format='$,.0f')),
        color='Series:N',
        tooltip=['Series', alt.Tooltip('Payor gross ($/yr):Q', format='$,.0f'),
                 alt.Tooltip('$/mo:Q', format='$,.0f')],
    ).properties(height=380)
    rule_p = alt.Chart(pd.DataFrame({'x': [G_p]})).mark_rule(color='#888', strokeDash=[4,4]).encode(x='x:Q')
    st.altair_chart(chart_p + rule_p, use_container_width=True)
    st.caption(
        "Verifies user constraint #2 (no-cross): payor's take-home stays above "
        "Party A's at every income level, with growing margin. Vertical dashed line "
        "marks current G_p."
    )

# ---------------------------------------------------------------------------
# Methodology + footer
# ---------------------------------------------------------------------------
with st.expander("Methodology — how the formula works"):
    st.markdown(f"""
**Two-stage computation.**

**1 · Child support (NC Worksheet B, mechanical).**
Implements [AOC-CV-628 (Worksheet B, Rev. 1/23)][wsb] line-by-line:

- **Lines 1–3.** Each parent's monthly gross adjusted income (line 2) and percentage share (line 3).
- **Line 4 — BCSO.** Looked up from the official [NC Schedule of Basic Support Obligations
  (AOC-A-162, Rev. 1/23)][a162] — all 774 published rows in $50 increments from $1,350 to $40,000/mo
  combined adjusted gross, for 1–6 children, with linear interpolation between adjacent rows.
  Below $1,350 the schedule's $50 minimum order applies; above $40,000 the schedule extrapolates
  at 50% of the cap-slope (a defensible "reasonable-needs partial uplift" per
  [G.S. 50-13.4(c)][nc5013]).
- **Line 5.** BCSO × 1.5 — the shared-custody multiplier.
- **Line 6.** Each parent's portion of line 5 by income share.
- **Line 9.** Each parent's basic obligation for time the children are with the OTHER parent
  (line 6 × other parent's overnight percentage).
- **Lines 10–11.** Combined direct add-ons (children's health insurance + work-related child care);
  each parent's "fair share" by income share.
- **Line 12.** Adjustments paid **in excess** of fair share. *Per the form, if negative enter zero* —
  so only the parent who overpaid gets a credit; the other parent gets no add-back. (This is the
  subtle bit that almost every off-the-shelf calculator gets wrong.)
- **Line 13.** Each parent's adjusted obligation (line 9 minus line 12).
- **Line 14.** Greater minus lesser; the higher-line-13 parent pays the difference to the other.

**2 · Alimony (calibrated economic optimum + legal gates).**
Interior formula:

A = (1 − w) · N(G_p)/12 − w_eff(G_a) · N(G_a)/12 − CS,

where N(·) is post-tax-post-FICA net income, **w = {W_BASE:.3f}** is calibrated to the user's anchor
($285K / $0 / 2 kids / 50-50 → $5K/mo), and w_eff(G_a) smoothly tapers from {W_BASE:.3f} at G_a=0 to 0.40
at high G_a to keep the recipient's marginal effective tax rate ≤ 65% (no benefit cliffs).

**Gate sequence (first to fire zeroes alimony):**

1. Dependency gate at {DEPENDENCY_GATE_RATIO*100:.0f}% of combined **net** income —
   operationalizes the "dependent spouse" finding under [NCGS 50-16.1A][nc161a].
   Net-income basis (not gross) because TCJA makes alimony non-deductible to payor
   and non-taxable to recipient, so "ability to pay" and "need" are properly
   measured post-tax. Threshold matches the AAML practitioner standard.
2. De-minimis $1,500/mo gross-gap floor.
3. Smooth self-sufficiency taper at 1.5 × FPL × (1 + 0.6n).
4. Compute interior, multiply by self-sufficiency factor.
5. No-cross post-hoc adjustment ($300/mo cushion).
6. Non-negative.

**Tax module.** 2025 single-filer federal brackets, NC 4.25% flat (drops to 3.99% in 2026),
full FICA including 0.9% Additional Medicare on income above $200,000.

**Post-TCJA treatment.** For divorces finalized after 12/31/2018, alimony is **not** deductible
to the payor and **not** taxable to the recipient ([IRC §11051][tcja]; NC conforms via federal AGI).
Every dollar of alimony in this model is post-tax cash from the payor.

**Validation against actual NC practice.** The Worksheet B implementation reproduces a real
attorney-prepared CV-628 (lawyer's worksheet, April 2026) to within $0.09 at exact 50/50
overnights, and within $3 at integer-overnight settings (the residual is pure overnight rounding).

See `MODEL.md` and `ORCHESTRATOR_REPORT.md` for the full derivation, agent disagreements,
and reconciliation rationale.

[wsb]: https://www.nccourts.gov/assets/documents/forms/cv628_0.pdf
[a162]: https://www.ncdhhs.gov/css2255a1/download
[nc5013]: https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_50/GS_50-13.4.html
[nc161a]: https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_50/GS_50-16.1A.html
[tcja]: https://www.irs.gov/taxtopics/tc452
""")

st.markdown(
    '<div class="small-muted">This is a planning/negotiation aid, not legal advice. NC alimony is judicial discretion bounded by 16 statutory factors; a judge can deviate from any formula. Consult an NC family-law attorney.</div>',
    unsafe_allow_html=True,
)
