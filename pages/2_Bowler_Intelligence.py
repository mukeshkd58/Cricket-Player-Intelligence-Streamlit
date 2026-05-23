from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import bar_chart, pie_chart
from src.data_loader import filter_deliveries, infer_player_team, load_bowler_summary, load_deliveries, load_matchups, load_phase_analysis, load_player_metadata
from src.feature_engineering import bowling_runs
from src.image_utils import render_player_card
from src.metrics import bowler_strengths_weaknesses
from src.ui_components import inject_global_css, no_data_box, render_metric_grid, render_section_header, sidebar_filters

st.set_page_config(page_title="Bowler Intelligence", page_icon="🎯", layout="wide")
inject_global_css()
st.title("🎯 Bowler Intelligence")

df = load_deliveries()
if df.empty:
    no_data_box(); st.stop()
filters = sidebar_filters(df, "bowl")
fdf = filter_deliveries(df, **filters)
if fdf.empty:
    st.warning("No deliveries match selected filters."); st.stop()
summary = load_bowler_summary()
players = sorted(fdf["bowler"].dropna().astype(str).unique())
player = st.selectbox("Select bowler", players)
player_df = fdf[fdf["bowler"].astype(str) == player]
row_df = summary[summary["bowler"].astype(str) == player] if not summary.empty else pd.DataFrame()
row = row_df.iloc[0].to_dict() if not row_df.empty else {}
team = infer_player_team(fdf, player)
metadata = load_player_metadata()
meta_bits = [team]
if not metadata.empty and "player" in metadata.columns:
    m = metadata[metadata["player"].astype(str) == player]
    if not m.empty:
        for col in ["bowling_style", "role"]:
            val = str(m.iloc[0].get(col, "")).strip()
            if val and val != "Data not available": meta_bits.append(val)
meta = " • ".join(meta_bits) if meta_bits else "Data not available"
balls = int(row.get("legal_balls", player_df.get("legal_ball", pd.Series(dtype=bool)).sum() if "legal_ball" in player_df.columns else len(player_df)))
render_player_card(
    player,
    meta,
    [
        ("Wickets", f"{int(row.get('wickets', 0)):,}"),
        ("Overs", f"{float(row.get('overs', 0)):.1f}"),
        ("Economy", f"{float(row.get('economy', 0)):.2f}"),
        ("Average", f"{float(row.get('average', 0)):.2f}"),
        ("Dot %", f"{float(row.get('dot_ball_pct', 0)):.1f}%"),
        ("Boundary conceded %", f"{float(row.get('boundary_conceded_pct', 0)):.1f}%"),
    ],
)
if balls < 60:
    st.warning("Small sample size warning: this bowler has fewer than 60 legal balls in the current filter.")

render_metric_grid([
    ("Threat score", f"{float(row.get('threat_score', 0)):.1f}", "Dot-ball + wicket + boundary prevention"),
    ("Wicket rate", f"{float(row.get('wicket_rate_pct', 0)):.2f}%", "Bowler-attributed wickets per legal ball"),
    ("Boundary risk", f"{float(row.get('boundary_risk_score', 0)):.1f}", "Boundary conceded scaled to 0–100"),
    ("Strike rate", f"{float(row.get('strike_rate', 0)):.1f}", "Balls per wicket"),
])

matchups = load_matchups()
strengths, weaknesses, plan = bowler_strengths_weaknesses(player, fdf, matchups)
col1, col2, col3 = st.columns(3)
with col1:
    render_section_header("Top Strengths")
    for x in strengths: st.success(x)
with col2:
    render_section_header("Weakness Areas")
    for x in weaknesses: st.error(x)
with col3:
    render_section_header("Tactical Bowling Plan")
    for x in plan: st.info(x)

phase = load_phase_analysis()
bp = phase[(phase.get("entity_type", "") == "bowler") & (phase.get("player", "").astype(str) == player)] if not phase.empty else pd.DataFrame()
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(bar_chart(bp, "phase", "economy", "Economy by Phase"), use_container_width=True)
with col2:
    st.plotly_chart(bar_chart(bp, "phase", "dot_ball_pct", "Dot Ball % by Phase"), use_container_width=True)

render_section_header("Wicket Types")
wickets = player_df[player_df.get("is_bowler_wicket", False).astype(bool)] if "is_bowler_wicket" in player_df.columns else pd.DataFrame()
if wickets.empty:
    st.info("No bowler-attributed wickets available for this bowler in current filter.")
else:
    wk = wickets.groupby("wicket_type").size().reset_index(name="count")
    st.plotly_chart(pie_chart(wk, "wicket_type", "count", "Wicket Type Pattern"), use_container_width=True)

render_section_header("Best and Worst Matchups")
pm = matchups[matchups["bowler"].astype(str) == player] if not matchups.empty and "bowler" in matchups.columns else pd.DataFrame()
pm = pm[pm["balls"] >= 12] if not pm.empty and "balls" in pm.columns else pm
if pm.empty:
    st.info("No matchup with at least 12 balls found in current processed data.")
else:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Bowler-dominant matchups**")
        st.dataframe(pm.sort_values("risk_score", ascending=False).head(10), use_container_width=True)
    with c2:
        st.markdown("**Batter-dominant matchups against this bowler**")
        st.dataframe(pm.sort_values("dominance_score", ascending=False).head(10), use_container_width=True)
