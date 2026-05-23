from __future__ import annotations

import streamlit as st

from src.data_loader import load_batter_summary, load_bowler_summary, load_deliveries, load_matchups, safe_unique
from src.report_generator import export_report_pdf, make_tactical_report
from src.ui_components import inject_global_css, no_data_box, render_section_header

st.set_page_config(page_title="Export Report", page_icon="📤", layout="wide")
inject_global_css()
st.title("📤 Export Reports and CSV Summaries")

df = load_deliveries()
if df.empty:
    no_data_box(); st.stop()
matchups = load_matchups()
role = st.radio("PDF report type", ["Batter", "Bowler"], horizontal=True)
players = safe_unique(df, "batter" if role == "Batter" else "bowler")
player = st.selectbox("Select player", players)
if st.button("Create player tactical PDF"):
    report = make_tactical_report(player, role, df, matchups)
    path = export_report_pdf(report)
    st.success(f"Created {path.name}")
    st.download_button("Download player report PDF", data=path.read_bytes(), file_name=path.name, mime="application/pdf")

render_section_header("CSV Exports")
for name, table in [
    ("deliveries.csv", df),
    ("batting_player_summary.csv", load_batter_summary()),
    ("bowling_player_summary.csv", load_bowler_summary()),
    ("batter_vs_bowler_matchups.csv", matchups),
]:
    if table.empty: continue
    st.download_button(f"Download {name}", data=table.to_csv(index=False).encode("utf-8"), file_name=name, mime="text/csv")

render_section_header("PNG Charts")
st.info("PNG chart export requires Plotly Kaleido. The app focuses on PDF and CSV export by default to keep deployment stable.")
