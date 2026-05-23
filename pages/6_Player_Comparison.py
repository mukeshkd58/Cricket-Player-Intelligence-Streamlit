from __future__ import annotations

import streamlit as st

from src.charts import radar_chart
from src.data_loader import load_batter_summary, load_bowler_summary, load_deliveries, safe_unique
from src.image_utils import render_player_card
from src.ui_components import inject_global_css, no_data_box, render_section_header

st.set_page_config(page_title="Player Comparison", page_icon="🆚", layout="wide")
inject_global_css()
st.title("🆚 Player Comparison")

df = load_deliveries()
if df.empty:
    no_data_box(); st.stop()
mode = st.radio("Compare", ["Batters", "Bowlers"], horizontal=True)
if mode == "Batters":
    summary = load_batter_summary(); key = "batter"
    metrics = ["runs", "strike_rate", "average", "boundary_pct", "consistency_score"]
else:
    summary = load_bowler_summary(); key = "bowler"
    metrics = ["wickets", "economy", "average", "dot_ball_pct", "threat_score"]
if summary.empty:
    st.warning("Summary file missing. Run python scripts/build_player_features.py"); st.stop()
players = sorted(summary[key].dropna().astype(str).unique())
c1, c2 = st.columns(2)
with c1: p1 = st.selectbox("Player 1", players, index=0)
with c2: p2 = st.selectbox("Player 2", players, index=min(1, len(players)-1))
r1 = summary[summary[key].astype(str) == p1].iloc[0]
r2 = summary[summary[key].astype(str) == p2].iloc[0]

c1, c2 = st.columns(2)
with c1:
    render_player_card(p1, mode[:-1], [(m, f"{r1.get(m, 0):.2f}" if isinstance(r1.get(m, 0), float) else r1.get(m, 0)) for m in metrics], image_note=False)
with c2:
    render_player_card(p2, mode[:-1], [(m, f"{r2.get(m, 0):.2f}" if isinstance(r2.get(m, 0), float) else r2.get(m, 0)) for m in metrics], image_note=False)

render_section_header("KPI Comparison")
compare = summary[summary[key].astype(str).isin([p1, p2])][[key] + [m for m in metrics if m in summary.columns]]
st.dataframe(compare, use_container_width=True)

# Normalize radar scores without faking values; only scales observed metrics for comparison visual.
labels, v1, v2 = [], [], []
for m in metrics:
    if m not in summary.columns: continue
    col = summary[m].astype(float)
    lo, hi = col.quantile(.05), col.quantile(.95)
    def norm(x):
        if hi == lo: return 50.0
        score = (float(x) - lo) / (hi - lo) * 100
        if mode == "Bowlers" and m in ["economy", "average"]:
            score = 100 - score
        return max(0, min(100, score))
    labels.append(m.replace("_", " ").title()); v1.append(norm(r1[m])); v2.append(norm(r2[m]))
st.plotly_chart(radar_chart(labels, v1, p1, v2, p2, "Scaled KPI Radar (relative to processed data)"), use_container_width=True)
st.info("Radar values are scaled from the real processed dataset for visual comparison. They are not invented cricket statistics.")
