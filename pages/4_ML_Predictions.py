from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data_loader import load_deliveries, safe_unique
from src.model_utils import FEATURE_COLUMNS, load_metrics, predict_probability, train_all_models
from src.ui_components import inject_global_css, no_data_box, render_metric_grid, render_section_header

st.set_page_config(page_title="ML Predictions", page_icon="🧠", layout="wide")
inject_global_css()
st.title("🧠 Machine Learning Weakness Prediction")

df = load_deliveries()
if df.empty:
    no_data_box(); st.stop()

render_section_header("Model Training Status", "Models are trained only from processed real Cricsheet deliveries.")
for target in ["batter_dismissal", "boundary_probability", "bowler_wicket"]:
    m = load_metrics(target)
    if not m:
        st.warning(f"{target}: model not trained yet. Run python scripts/train_models.py or use the button below.")
    elif m.get("status") == "trained":
        render_metric_grid([
            (target, m.get("model_type", "model"), f"Rows: {m.get('rows', 0):,}"),
            ("Accuracy", f"{m.get('accuracy', 0):.3f}", None),
            ("Precision", f"{m.get('precision', 0):.3f}", None),
            ("Recall", f"{m.get('recall', 0):.3f}", None),
            ("F1", f"{m.get('f1', 0):.3f}", None),
            ("ROC-AUC", f"{m.get('roc_auc', 0):.3f}" if m.get("roc_auc") is not None else "NA", None),
        ], columns=3)
    else:
        st.info(f"{target}: {m.get('reason', 'not trained')}")

if st.button("Train / retrain models from real processed data"):
    with st.spinner("Training models from processed deliveries..."):
        results = train_all_models(df)
    st.success("Training command finished. Refresh page to reload metrics.")
    st.json(results)

render_section_header("Interactive Matchup Probability", "Select a scenario and score dismissal/boundary/wicket probabilities.")
batters = safe_unique(df, "batter")
bowlers = safe_unique(df, "bowler")
teams = sorted(set(safe_unique(df, "batting_team") + safe_unique(df, "bowling_team")))
formats = safe_unique(df, "match_type")
phases = safe_unique(df, "phase")
c1, c2, c3 = st.columns(3)
with c1:
    batter = st.selectbox("Batter", batters)
    batting_team = st.selectbox("Batting team", teams)
with c2:
    bowler = st.selectbox("Bowler", bowlers)
    bowling_team = st.selectbox("Bowling team", teams)
with c3:
    match_type = st.selectbox("Format", formats)
    phase = st.selectbox("Phase", phases)
    over = st.number_input("Over", min_value=0, max_value=200, value=10)
    innings = st.number_input("Innings", min_value=1, max_value=4, value=1)
row = {"batter": batter, "bowler": bowler, "batting_team": batting_team, "bowling_team": bowling_team, "match_type": match_type, "phase": phase, "over": over, "innings": innings}
probs = {target: predict_probability(target, row) for target in ["batter_dismissal", "boundary_probability", "bowler_wicket"]}
render_metric_grid([
    ("Batter dismissal risk", "Model missing" if probs["batter_dismissal"] is None else f"{probs['batter_dismissal']*100:.1f}%", "Probability of selected batter being dismissed on a delivery"),
    ("Boundary probability", "Model missing" if probs["boundary_probability"] is None else f"{probs['boundary_probability']*100:.1f}%", "Probability of 4/6 from batter"),
    ("Bowler wicket probability", "Model missing" if probs["bowler_wicket"] is None else f"{probs['bowler_wicket']*100:.1f}%", "Bowler-attributed wicket probability"),
], columns=3)
st.info("Interpretation: these ML scores are delivery-level portfolio models, not guaranteed professional scouting truth. Use them as evidence signals alongside matchup and phase analytics.")
