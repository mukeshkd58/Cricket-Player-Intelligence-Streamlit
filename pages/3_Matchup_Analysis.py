from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import bar_chart
from src.data_loader import filter_deliveries, load_deliveries, load_matchups
from src.feature_engineering import add_derived_delivery_features
from src.image_utils import render_player_card
from src.ui_components import inject_global_css, no_data_box, render_metric_grid, render_section_header, sidebar_filters

st.set_page_config(page_title="Matchup Analysis", page_icon="⚔️", layout="wide")
inject_global_css()
st.title("⚔️ Batter vs Bowler Matchup Analysis")

df = load_deliveries()
if df.empty:
    no_data_box(); st.stop()
filters = sidebar_filters(df, "matchup")
fdf = filter_deliveries(df, **filters)
if fdf.empty:
    st.warning("No deliveries match selected filters."); st.stop()

batters = sorted(fdf["batter"].dropna().astype(str).unique())
bowlers = sorted(fdf["bowler"].dropna().astype(str).unique())
c1, c2 = st.columns(2)
with c1:
    batter = st.selectbox("Select batter", batters)
with c2:
    bowler = st.selectbox("Select bowler", bowlers)

matchups = load_matchups()
row_df = matchups[(matchups["batter"].astype(str) == batter) & (matchups["bowler"].astype(str) == bowler)] if not matchups.empty else pd.DataFrame()
mdf = add_derived_delivery_features(fdf[(fdf["batter"].astype(str) == batter) & (fdf["bowler"].astype(str) == bowler)])
if row_df.empty and not mdf.empty:
    legal = mdf[mdf["legal_ball"].astype(bool)]
    row = {
        "balls": int(legal.shape[0]),
        "runs": int(legal["runs_batter"].sum()),
        "dismissals": int((legal.get("player_out", "").astype(str) == batter).sum()) if "player_out" in legal.columns else 0,
        "dot_balls": int(legal["is_dot"].sum()),
        "boundaries": int(legal["is_boundary"].sum()),
    }
    row["strike_rate"] = round(row["runs"] * 100 / row["balls"], 2) if row["balls"] else 0
    row["risk_score"] = 0
    row["matchup_winner"] = "Data not available"
elif not row_df.empty:
    row = row_df.iloc[0].to_dict()
else:
    row = {"balls": 0, "runs": 0, "dismissals": 0, "dot_balls": 0, "boundaries": 0, "strike_rate": 0, "risk_score": 0, "matchup_winner": "No data"}

c1, c2 = st.columns(2)
with c1:
    render_player_card(batter, "Batter", [("Runs vs bowler", row["runs"]), ("Balls", row["balls"]), ("SR", row["strike_rate"])], image_note=False)
with c2:
    render_player_card(bowler, "Bowler", [("Dismissals", row["dismissals"]), ("Dot balls", row["dot_balls"]), ("Risk score", row.get("risk_score", 0))], image_note=False)

render_metric_grid([
    ("Runs", row["runs"], None),
    ("Balls", row["balls"], None),
    ("Dismissals", row["dismissals"], None),
    ("Strike rate", f"{float(row['strike_rate']):.2f}", None),
    ("Dot balls", row["dot_balls"], None),
    ("Boundaries", row["boundaries"], None),
    ("Risk score", f"{float(row.get('risk_score', 0)):.1f}", "Higher favours bowler"),
    ("Winner", row.get("matchup_winner", "Data not available"), None),
], columns=4)

if int(row["balls"]) < 12:
    st.warning("Small sample size: fewer than 12 legal balls in this matchup. Treat the interpretation carefully.")

render_section_header("Tactical Explanation")
if row.get("matchup_winner") == "Batter":
    st.success(f"{batter} has the statistical edge. Batter plan: keep strike rotation active and attack balls in scoring zones after settling.")
    st.info(f"{bowler} plan: increase dot-ball pressure early, use field protection for boundary options, and change pace/angle before the batter settles.")
elif row.get("matchup_winner") == "Bowler":
    st.success(f"{bowler} has the statistical edge. Bowler plan: repeat the pressure pattern and attack dismissal mode early.")
    st.info(f"{batter} plan: reduce dot-ball clusters, avoid early high-risk shots, and target safer singles until the bowler changes length.")
else:
    st.info("Not enough real matchup data to declare a reliable edge.")

render_section_header("Ball-by-Ball Matchup Events")
if mdf.empty:
    st.info("No ball-by-ball records for selected matchup in current filters.")
else:
    event = mdf.groupby("over").agg(runs=("runs_batter", "sum"), balls=("legal_ball", "sum"), dots=("is_dot", "sum"), boundaries=("is_boundary", "sum")).reset_index()
    st.plotly_chart(bar_chart(event, "over", "runs", "Runs by Over in Matchup"), use_container_width=True)
    st.dataframe(mdf[[c for c in ["date", "match_type", "batting_team", "bowling_team", "venue", "over", "ball", "runs_batter", "runs_total", "wicket_type", "player_out"] if c in mdf.columns]].head(200), use_container_width=True)
