from __future__ import annotations

import streamlit as st

from src.data_loader import load_deliveries, load_matchups, safe_unique
from src.report_generator import export_report_pdf, make_tactical_report
from src.ui_components import inject_global_css, no_data_box, render_section_header

st.set_page_config(page_title="AI Tactical Report", page_icon="📋", layout="wide")
inject_global_css()
st.title("📋 AI Tactical Report")

df = load_deliveries()
if df.empty:
    no_data_box(); st.stop()
matchups = load_matchups()
role = st.radio("Report type", ["Batter", "Bowler"], horizontal=True)
players = safe_unique(df, "batter" if role == "Batter" else "bowler")
player = st.selectbox("Select player", players)
report = make_tactical_report(player, role, df, matchups)

render_section_header(report["title"], f"Generated for {report['player']} from {report['data_source']}")
st.markdown(f"**Team:** {report['team']}  |  **Sample size:** {report['sample_size']} deliveries  |  **Confidence:** {report['confidence']}")
cols = st.columns(3)
sections = [("Top Strengths", "strengths"), ("Top Weaknesses", "weaknesses"), ("Tactical Plan", "tactical_plan")]
for col, (title, key) in zip(cols, sections):
    with col:
        render_section_header(title)
        for item in report[key]:
            st.write("-", item)
render_section_header("Training Recommendations")
for item in report["training_recommendations"]:
    st.info(item)
render_section_header("Limitations")
for item in report["limitations"]:
    st.warning(item)

if st.button("Generate PDF report"):
    path = export_report_pdf(report)
    st.success(f"PDF created: {path}")
    st.download_button("Download PDF", data=path.read_bytes(), file_name=path.name, mime="application/pdf")
