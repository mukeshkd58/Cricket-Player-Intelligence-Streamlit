from __future__ import annotations

import html
from typing import Sequence

import pandas as pd
import streamlit as st


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #06130d;
            --panel: rgba(14, 35, 24, 0.78);
            --panel-2: rgba(18, 54, 36, 0.62);
            --text: #eef9f1;
            --muted: rgba(238,249,241,.70);
            --gold: #f5c66b;
            --green: #4ee28a;
            --danger: #ff7b7b;
            --line: rgba(255,255,255,.12);
        }
        .stApp {
            background:
              radial-gradient(circle at 15% 5%, rgba(64, 214, 116, .22), transparent 28%),
              radial-gradient(circle at 85% 15%, rgba(245, 198, 107, .12), transparent 24%),
              linear-gradient(135deg, #020604 0%, #08170f 42%, #0b2417 100%);
            color: var(--text);
        }
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image:
              linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px),
              linear-gradient(0deg, rgba(255,255,255,.025) 1px, transparent 1px);
            background-size: 52px 52px;
            mask-image: linear-gradient(to bottom, black, transparent 70%);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(4,12,8,.98), rgba(10,35,22,.96));
            border-right: 1px solid rgba(78,226,138,.16);
        }
        h1, h2, h3 { color: #f6fff8; letter-spacing: -.03em; }
        .hero-pro {
            padding: 2rem 2rem;
            border: 1px solid rgba(78,226,138,.22);
            border-radius: 28px;
            background:
              linear-gradient(135deg, rgba(19, 72, 43, .86), rgba(5, 15, 10, .74)),
              radial-gradient(circle at 80% 20%, rgba(245,198,107,.22), transparent 22%);
            box-shadow: 0 24px 80px rgba(0,0,0,.28);
            margin-bottom: 1.35rem;
        }
        .hero-kicker { color: var(--gold); text-transform: uppercase; font-weight: 800; letter-spacing: .12em; font-size: .82rem; }
        .hero-pro h1 { font-size: clamp(2rem, 5vw, 4.4rem); line-height: .95; margin: .4rem 0 .8rem 0; }
        .hero-pro p { color: var(--muted); font-size: 1.05rem; max-width: 880px; }
        .badge-row { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1rem; }
        .badge-pro, .data-badge {
            display: inline-flex; align-items: center; gap: .35rem;
            padding: .42rem .7rem; border-radius: 999px;
            border: 1px solid rgba(78,226,138,.25);
            background: rgba(8, 26, 16, .62);
            color: #dffff0; font-weight: 700; font-size: .82rem;
        }
        .data-badge { border-color: rgba(245,198,107,.35); color: #ffe8b4; }
        .glass-card, .metric-card-pro, .player-card {
            border: 1px solid var(--line);
            background: linear-gradient(145deg, rgba(15, 45, 29, .76), rgba(5, 14, 9, .62));
            border-radius: 22px;
            padding: 1rem;
            box-shadow: 0 14px 38px rgba(0,0,0,.24);
        }
        .metric-card-pro { min-height: 110px; }
        .metric-label { color: var(--muted); font-size: .82rem; text-transform: uppercase; letter-spacing: .08em; font-weight: 700; }
        .metric-value { color: #fff; font-size: 1.85rem; font-weight: 900; margin-top: .45rem; }
        .metric-help { color: rgba(238,249,241,.62); font-size: .78rem; margin-top: .25rem; }
        .section-title { margin: 1.2rem 0 .55rem 0; color: #f5c66b; font-size: 1.15rem; font-weight: 900; letter-spacing: -.01em; }
        .section-subtitle { color: var(--muted); margin-top: -.4rem; margin-bottom: .8rem; }
        .feature-icon { font-size: 2rem; margin-bottom: .55rem; }
        .feature-title { font-size: 1.05rem; font-weight: 900; color: #ffffff; }
        .feature-copy { color: var(--muted); font-size: .9rem; margin-top: .35rem; }
        .player-card-head { display: flex; align-items: center; gap: 1rem; }
        .player-avatar, .player-avatar-fallback {
            width: 104px; height: 104px; border-radius: 28px;
            border: 1px solid rgba(245,198,107,.28);
            object-fit: cover;
            background: linear-gradient(135deg, rgba(78,226,138,.26), rgba(245,198,107,.18));
        }
        .player-avatar-fallback { display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 900; color: #fff; }
        .player-name { font-size: 1.55rem; font-weight: 950; color: #fff; }
        .player-meta { color: var(--muted); font-weight: 650; }
        .small-note { color: rgba(238,249,241,.68); font-size: .88rem; }
        .warning-card { border: 1px solid rgba(245,198,107,.28); background: rgba(110,75,15,.18); border-radius: 18px; padding: .9rem; }
        .danger-text { color: var(--danger); font-weight: 800; }
        .success-text { color: var(--green); font-weight: 800; }
        .stDataFrame { border-radius: 18px; overflow: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f'<div class="section-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{html.escape(subtitle)}</div>', unsafe_allow_html=True)


def render_metric_grid(items: Sequence[tuple[str, str, str | None]], columns: int = 4) -> None:
    cols = st.columns(columns)
    for idx, (label, value, help_text) in enumerate(items):
        with cols[idx % columns]:
            help_html = f'<div class="metric-help">{html.escape(help_text)}</div>' if help_text else ""
            st.markdown(
                f"""
                <div class="metric-card-pro">
                  <div class="metric-label">{html.escape(label)}</div>
                  <div class="metric-value">{html.escape(str(value))}</div>
                  {help_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_feature_card(title: str, copy: str, icon: str = "🏏") -> None:
    st.markdown(
        f"""
        <div class="glass-card">
          <div class="feature-icon">{html.escape(icon)}</div>
          <div class="feature-title">{html.escape(title)}</div>
          <div class="feature-copy">{html.escape(copy)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_status(df: pd.DataFrame) -> None:
    try:
        from src.data_loader import get_active_data_mode
        mode = get_active_data_mode()
    except Exception:
        mode = "missing" if df.empty else "loaded"

    if df.empty:
        label = "Data status: processed/sample Cricsheet data missing"
    elif mode == "sample":
        label = "Data status: real sample Cricsheet data loaded for cloud demo"
    elif mode == "full":
        label = "Data status: full real processed Cricsheet data loaded"
    else:
        label = "Data status: real Cricsheet data loaded"
    st.markdown(f'<span class="data-badge">{html.escape(label)}</span>', unsafe_allow_html=True)


def no_data_box() -> None:
    st.error("No deliveries found at data/processed/deliveries.csv or data/sample/deliveries_sample.csv.")
    st.info("For the full dataset, run: python scripts/download_cricsheet_data.py → python scripts/process_cricsheet_data.py → python scripts/build_player_features.py")


def sidebar_filters(df: pd.DataFrame, key_prefix: str = "global") -> dict:
    filters: dict = {"formats": [], "teams": [], "years": [], "venues": [], "phases": []}
    if df.empty:
        return filters
    with st.sidebar:
        st.markdown("### Filters")
        if "match_type" in df.columns:
            opts = sorted(df["match_type"].dropna().astype(str).unique())
            filters["formats"] = st.multiselect("Format", opts, default=opts, key=f"{key_prefix}_formats")
        if {"batting_team", "bowling_team"}.issubset(df.columns):
            opts = sorted(set(df["batting_team"].dropna().astype(str)).union(set(df["bowling_team"].dropna().astype(str))))
            filters["teams"] = st.multiselect("Team", opts, key=f"{key_prefix}_teams")
        if "year" in df.columns:
            years = sorted(pd.to_numeric(df["year"], errors="coerce").dropna().astype(int).unique())
            default_years = years[-6:] if len(years) > 6 else years
            filters["years"] = st.multiselect("Year", years, default=default_years, key=f"{key_prefix}_years")
        if "venue" in df.columns:
            venues = sorted(df["venue"].dropna().astype(str).unique())
            filters["venues"] = st.multiselect("Venue", venues, key=f"{key_prefix}_venues")
        if "phase" in df.columns:
            phases = ["Powerplay", "Middle", "Death", "Long-format"]
            existing = [p for p in phases if p in set(df["phase"].dropna().astype(str).unique())]
            filters["phases"] = st.multiselect("Phase", existing, default=existing, key=f"{key_prefix}_phases")
    return filters
