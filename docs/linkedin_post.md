# LinkedIn Post Draft

I built a portfolio prototype of a **Cricket Player Strength & Weakness Intelligence Platform** using real Cricsheet ball-by-ball data.

The goal is not match-winner prediction. The goal is closer to real cricket analyst workflows:

- batter strength and weakness diagnosis
- bowler threat profiling
- phase-wise performance analysis
- batter vs bowler matchup cards
- ML-based dismissal/boundary/wicket risk signals
- scouting-style tactical reports
- PDF and CSV exports
- real player image support via Wikidata/Wikimedia Commons where available

I kept the data rules strict: no fake players, no random demo statistics, and no Google Images scraping. If a field like bowling style, batting hand, line/length or shot zone is not present in the real data, the app marks it as unavailable instead of inventing it.

Tech stack: Python, Streamlit, Pandas, NumPy, Scikit-learn, Plotly, ReportLab, Cricsheet JSON, Wikidata/Wikimedia APIs.

This project helped me practice sports data science, cricket analytics, ML feature engineering, dashboard UI/UX, tactical storytelling, and portfolio-grade deployment structure.
