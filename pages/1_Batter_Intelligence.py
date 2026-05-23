from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import bar_chart, pie_chart
from src.data_loader import filter_deliveries, infer_player_team, load_batter_summary, load_deliveries, load_matchups, load_phase_analysis, load_player_metadata
from src.image_utils import render_player_card
from src.metrics import batter_strengths_weaknesses
from src.ui_components import inject_global_css, no_data_box, render_metric_grid, render_section_header, sidebar_filters

st.set_page_config(page_title="Batter Intelligence", page_icon="🏏", layout="wide")
inject_global_css()
st.title("🏏 Batter Intelligence")

df = load_deliveries()
if df.empty:
    no_data_box(); st.stop()
filters = sidebar_filters(df, "bat")
fdf = filter_deliveries(df, **filters)
if fdf.empty:
    st.warning("No deliveries match selected filters."); st.stop()
summary = load_batter_summary()
if summary.empty:
    st.warning("Batter summary missing. Run python scripts/build_player_features.py"); st.stop()
players = sorted(fdf["batter"].dropna().astype(str).unique())
player = st.selectbox("Select batter", players)
player_df = fdf[fdf["batter"].astype(str) == player]
row_df = summary[summary["batter"].astype(str) == player]
row = row_df.iloc[0].to_dict() if not row_df.empty else {}
team = infer_player_team(fdf, player)
metadata = load_player_metadata()
meta_bits = [team]
if not metadata.empty and "player" in metadata.columns:
    m = metadata[metadata["player"].astype(str) == player]
    if not m.empty:
        for col in ["batting_hand", "role"]:
            val = str(m.iloc[0].get(col, "")).strip()
            if val and val != "Data not available": meta_bits.append(val)
meta = " • ".join(meta_bits) if meta_bits else "Data not available"

balls = int(row.get("balls", player_df.get("legal_ball", pd.Series(dtype=bool)).sum() if "legal_ball" in player_df.columns else len(player_df)))
render_player_card(
    player,
    meta,
    [
        ("Runs", f"{int(row.get('runs', 0)):,}"),
        ("Balls", f"{balls:,}"),
        ("Average", f"{float(row.get('average', 0)):.2f}"),
        ("Strike rate", f"{float(row.get('strike_rate', 0)):.2f}"),
        ("Dot %", f"{float(row.get('dot_ball_pct', 0)):.1f}%"),
        ("Boundary %", f"{float(row.get('boundary_pct', 0)):.1f}%"),
    ],
)
if balls < 60:
    st.warning("Small sample size warning: this batter has fewer than 60 legal balls in the current filter.")

render_metric_grid([
    ("Weakness score", f"{float(row.get('weakness_score', 0)):.1f}", "Higher = more dot-ball/dismissal vulnerability"),
    ("Pressure index", f"{float(row.get('pressure_index', 0)):.1f}", "Dot-ball + dismissal pressure"),
    ("Dismissal vulnerability", f"{float(row.get('dismissal_vulnerability_score', 0)):.1f}", "Dismissals per ball scaled to 0–100"),
    ("Consistency", f"{float(row.get('consistency_score', 0)):.1f}", "Lower volatility across innings"),
])

matchups = load_matchups()
strengths, weaknesses, plan = batter_strengths_weaknesses(player, fdf, matchups)
col1, col2, col3 = st.columns(3)
with col1:
    render_section_header("Top Strengths")
    for x in strengths: st.success(x)
with col2:
    render_section_header("Weakness Areas")
    for x in weaknesses: st.error(x)
with col3:
    render_section_header("Opposition Tactical Plan")
    for x in plan: st.info(x)

phase = load_phase_analysis()
bp = phase[(phase.get("entity_type", "") == "batter") & (phase.get("player", "").astype(str) == player)] if not phase.empty else pd.DataFrame()
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(bar_chart(bp, "phase", "strike_rate", "Strike Rate by Phase"), use_container_width=True)
with col2:
    st.plotly_chart(bar_chart(bp, "phase", "dot_ball_pct", "Dot Ball % by Phase"), use_container_width=True)

render_section_header("Dismissal Types")
dismissals = player_df[player_df.get("player_out", "").astype(str) == player] if "player_out" in player_df.columns else pd.DataFrame()
if dismissals.empty:
    st.info("No dismissal records available for this batter in current filter.")
else:
    dis = dismissals.groupby("wicket_type").size().reset_index(name="count")
    st.plotly_chart(pie_chart(dis, "wicket_type", "count", "Dismissal Pattern"), use_container_width=True)

render_section_header("Bowling Type / Line-Length")
st.info("Bowling-style and line/length analysis requires real enrichment metadata. Cricsheet ball-by-ball does not reliably include bowling type, batting hand, shot type, or line/length. The app will not invent these fields.")

render_section_header("Best and Worst Matchups")
pm = matchups[matchups["batter"].astype(str) == player] if not matchups.empty and "batter" in matchups.columns else pd.DataFrame()
pm = pm[pm["balls"] >= 12] if not pm.empty and "balls" in pm.columns else pm
if pm.empty:
    st.info("No matchup with at least 12 balls found in current processed data.")
else:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Best scoring matchups**")
        st.dataframe(pm.sort_values("dominance_score", ascending=False).head(10), use_container_width=True)
    with c2:
        st.markdown("**Highest risk matchups**")
        st.dataframe(pm.sort_values("risk_score", ascending=False).head(10), use_container_width=True)
