from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
try:
    import streamlit as st
except ModuleNotFoundError:  # allows non-UI unit tests before installing Streamlit
    class _NoopCache:
        def __call__(self, *args, **kwargs):
            def deco(fn):
                return fn
            return deco
    class _NoopStreamlit:
        cache_data = _NoopCache()
    st = _NoopStreamlit()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"
RAW_DIR = DATA_DIR / "raw"
IMAGES_DIR = DATA_DIR / "images"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"

DELIVERIES_PATH = PROCESSED_DIR / "deliveries.csv"
BALL_BY_BALL_PATH = PROCESSED_DIR / "ball_by_ball.csv"
BATTER_SUMMARY_PATH = PROCESSED_DIR / "batting_player_summary.csv"
BOWLER_SUMMARY_PATH = PROCESSED_DIR / "bowling_player_summary.csv"
MATCHUPS_PATH = PROCESSED_DIR / "batter_vs_bowler_matchups.csv"
PHASE_ANALYSIS_PATH = PROCESSED_DIR / "phase_analysis.csv"
VENUE_ANALYSIS_PATH = PROCESSED_DIR / "venue_analysis.csv"
PLAYER_IMAGE_MAP_PATH = PROCESSED_DIR / "player_image_map.csv"
PLAYER_METADATA_PATH = PROCESSED_DIR / "player_metadata.csv"


def ensure_dirs() -> None:
    for path in [DATA_DIR, RAW_DIR, PROCESSED_DIR, SAMPLE_DIR, IMAGES_DIR, MODELS_DIR, REPORTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def sample_path_for(processed_path: Path) -> Path:
    """Return the matching real sample CSV path for a processed data file."""
    return SAMPLE_DIR / f"{processed_path.stem}_sample{processed_path.suffix}"


def resolve_data_path(processed_path: Path) -> Path:
    """Prefer full processed data locally; fall back to real sample data for cloud demos."""
    processed_path = Path(processed_path)
    if processed_path.exists() and processed_path.stat().st_size > 0:
        return processed_path
    sample_path = sample_path_for(processed_path)
    if sample_path.exists() and sample_path.stat().st_size > 0:
        return sample_path
    return processed_path


def get_active_data_mode() -> str:
    """Human-readable status for the delivery data currently available to the app."""
    if DELIVERIES_PATH.exists() and DELIVERIES_PATH.stat().st_size > 0:
        return "full"
    sample = sample_path_for(DELIVERIES_PATH)
    if sample.exists() and sample.stat().st_size > 0:
        return "sample"
    return "missing"


@st.cache_data(show_spinner=False)
def read_csv_cached(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except Exception:
        return pd.DataFrame()


def load_deliveries() -> pd.DataFrame:
    ensure_dirs()
    return read_csv_cached(str(resolve_data_path(DELIVERIES_PATH)))


def load_batter_summary() -> pd.DataFrame:
    return read_csv_cached(str(resolve_data_path(BATTER_SUMMARY_PATH)))


def load_bowler_summary() -> pd.DataFrame:
    return read_csv_cached(str(resolve_data_path(BOWLER_SUMMARY_PATH)))


def load_matchups() -> pd.DataFrame:
    return read_csv_cached(str(resolve_data_path(MATCHUPS_PATH)))


def load_phase_analysis() -> pd.DataFrame:
    return read_csv_cached(str(resolve_data_path(PHASE_ANALYSIS_PATH)))


def load_venue_analysis() -> pd.DataFrame:
    return read_csv_cached(str(resolve_data_path(VENUE_ANALYSIS_PATH)))


def load_player_metadata() -> pd.DataFrame:
    return read_csv_cached(str(resolve_data_path(PLAYER_METADATA_PATH)))


def load_player_image_map() -> pd.DataFrame:
    # Prefer processed copy, then real sample copy, then static assets map.
    processed = read_csv_cached(str(resolve_data_path(PLAYER_IMAGE_MAP_PATH)))
    if not processed.empty:
        return processed
    assets = PROJECT_ROOT / "assets" / "player_images" / "player_image_map.csv"
    return read_csv_cached(str(assets))


def safe_unique(df: pd.DataFrame, col: str) -> list[str]:
    if df.empty or col not in df.columns:
        return []
    values = df[col].dropna().astype(str).str.strip()
    values = values[values != ""]
    return sorted(values.unique().tolist())


def filter_deliveries(
    df: pd.DataFrame,
    formats: Iterable[str] | None = None,
    teams: Iterable[str] | None = None,
    years: Iterable[int] | None = None,
    venues: Iterable[str] | None = None,
    phases: Iterable[str] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if formats and "match_type" in out.columns:
        out = out[out["match_type"].astype(str).isin(list(formats))]
    if teams and {"batting_team", "bowling_team"}.issubset(out.columns):
        teams_set = set(map(str, teams))
        out = out[out["batting_team"].astype(str).isin(teams_set) | out["bowling_team"].astype(str).isin(teams_set)]
    if years and "year" in out.columns:
        out = out[pd.to_numeric(out["year"], errors="coerce").isin(list(years))]
    if venues and "venue" in out.columns:
        out = out[out["venue"].astype(str).isin(list(venues))]
    if phases and "phase" in out.columns:
        out = out[out["phase"].astype(str).isin(list(phases))]
    return out


def load_metadata_summary(df: pd.DataFrame) -> dict[str, str | int]:
    if df.empty:
        return {"matches": 0, "players": 0, "formats": "Not available", "date_range": "Not available"}
    matches = int(df["match_id"].nunique()) if "match_id" in df.columns else 0
    players = set()
    if "batter" in df.columns:
        players.update(df["batter"].dropna().astype(str).unique().tolist())
    if "bowler" in df.columns:
        players.update(df["bowler"].dropna().astype(str).unique().tolist())
    formats = ", ".join(safe_unique(df, "match_type")[:8]) or "Not available"
    if "date" in df.columns:
        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        date_range = f"{dates.min().date()} → {dates.max().date()}" if not dates.empty else "Not available"
    else:
        date_range = "Not available"
    return {"matches": matches, "players": len(players), "formats": formats, "date_range": date_range}


def infer_player_team(df: pd.DataFrame, player: str) -> str:
    if df.empty:
        return "Data not available"
    frames = []
    if {"batter", "batting_team"}.issubset(df.columns):
        frames.append(df.loc[df["batter"].astype(str) == player, "batting_team"])
    if {"bowler", "bowling_team"}.issubset(df.columns):
        frames.append(df.loc[df["bowler"].astype(str) == player, "bowling_team"])
    if not frames:
        return "Data not available"
    values = pd.concat(frames).dropna().astype(str).str.strip()
    values = values[values != ""]
    if values.empty:
        return "Data not available"
    return values.mode().iloc[0]
