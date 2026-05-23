from __future__ import annotations

import streamlit as st

from src.data_loader import load_deliveries, load_metadata_summary
from src.ui_components import (
    inject_global_css,
    render_data_status,
    render_feature_card,
    render_metric_grid,
    render_section_header,
)

st.set_page_config(
    page_title="Cricket Player Intelligence",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

st.markdown(
    """
    <div class="hero-pro">
      <div class="hero-kicker">Real cricket ball-by-ball intelligence</div>
      <h1>Cricket Player Strength & Weakness Intelligence Platform</h1>
      <p>
        A professional Streamlit analytics workspace for batter weakness diagnosis,
        bowler threat profiling, matchup scouting, machine-learning risk scores, and
        coach-ready tactical reports using real Cricsheet data only.
      </p>
      <div class="badge-row">
        <span class="badge-pro">Real Cricsheet data</span>
        <span class="badge-pro">No fake players</span>
        <span class="badge-pro">Batter intelligence</span>
        <span class="badge-pro">Bowler intelligence</span>
        <span class="badge-pro">Matchup risk</span>
        <span class="badge-pro">PDF export</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


df = load_deliveries()
summary = load_metadata_summary(df)
render_data_status(df)

if df.empty:
    st.warning(
        "No real cricket data found yet. The app first looks for full processed data, then falls back to data/sample real demo extracts."
    )
    st.code(
        "pip install -r requirements.txt\n"
        "python scripts/download_cricsheet_data.py\n"
        "python scripts/process_cricsheet_data.py\n"
        "python scripts/build_player_features.py\n"
        "python scripts/fetch_player_images.py\n"
        "python scripts/train_models.py\n"
        "streamlit run app.py",
        language="bash",
    )
else:
    render_metric_grid(
        [
            ("Matches analyzed", f"{summary['matches']:,}", "Unique Cricsheet matches in processed deliveries"),
            ("Players", f"{summary['players']:,}", "Unique batters and bowlers"),
            ("Formats", summary["formats"], "Match types present in data"),
            ("Date range", summary["date_range"], "Based on match dates"),
        ]
    )

render_section_header("Command Center Modules", "Use the pages in the sidebar for player intelligence and reports.")
cols = st.columns(4)
with cols[0]:
    render_feature_card("Batter Intelligence", "Strength/weakness diagnosis, phase analysis, dismissal vulnerability, matchup trouble list.", "🏏")
with cols[1]:
    render_feature_card("Bowler Intelligence", "Threat score, phase control, economy leakage, wicket patterns, tactical plan.", "🎯")
with cols[2]:
    render_feature_card("Matchup Analysis", "Head-to-head runs, balls, dismissals, risk score, matchup winner, tactical explanation.", "⚔️")
with cols[3]:
    render_feature_card("ML + Reports", "Dismissal, boundary and wicket probability models plus PDF-ready scouting reports.", "🧠")

render_section_header("Data Integrity Rules", "This app intentionally avoids fake or scraped data.")
st.markdown(
    """
    <div class="glass-card">
      <ul>
        <li>Cricsheet JSON is the primary source for ball-by-ball cricket events.</li>
        <li>Cricsheet Register is used for identity mapping where available.</li>
        <li>Player images are fetched only from Wikidata/Wikimedia Commons image metadata; Google Images scraping is not used.</li>
        <li>If bowling style, batting hand, line/length, or shot zones are not available in the real data, the UI says <b>Data not available</b> instead of inventing values.</li>
      </ul>
    </div>
    """,
    unsafe_allow_html=True,
)
