from __future__ import annotations

import numpy as np
import pandas as pd

BOWLER_WICKET_TYPES = {
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "stumped",
    "hit wicket",
    "hit the ball twice",
}


def classify_phase(over: int | float | str, match_type: str | None = None) -> str:
    try:
        o = int(float(over))
    except Exception:
        return "Data not available"
    mt = str(match_type or "").lower()
    if mt in {"test", "mdm", "multi-day"}:
        return "Long-format"
    if o < 6:
        return "Powerplay"
    if o < 16:
        return "Middle"
    return "Death"


def add_derived_delivery_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    for col in ["runs_batter", "runs_total", "runs_extras"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
        else:
            out[col] = 0
    if "legal_ball" not in out.columns:
        if "extras_type" in out.columns:
            out["legal_ball"] = ~out["extras_type"].astype(str).str.contains("wides|no ball|no-balls|noballs", case=False, na=False)
        else:
            out["legal_ball"] = True
    out["is_dot"] = (out["runs_total"] == 0).astype(int)
    out["is_boundary"] = out["runs_batter"].isin([4, 6]).astype(int)
    if "wicket_type" not in out.columns:
        out["wicket_type"] = ""
    out["is_wicket"] = out.get("player_out", "").astype(str).str.strip().ne("").astype(int) if "player_out" in out.columns else 0
    out["is_bowler_wicket"] = out["wicket_type"].astype(str).str.lower().isin(BOWLER_WICKET_TYPES).astype(int)
    if "phase" not in out.columns:
        out["phase"] = [classify_phase(o, mt) for o, mt in zip(out.get("over", 0), out.get("match_type", ""))]
    if "year" not in out.columns and "date" in out.columns:
        out["year"] = pd.to_datetime(out["date"], errors="coerce").dt.year
    return out


def safe_div(num, den, default: float = 0.0) -> float:
    try:
        den = float(den)
        if den == 0 or np.isnan(den):
            return default
        return float(num) / den
    except Exception:
        return default


def pct(num, den) -> float:
    return round(safe_div(num, den) * 100, 2)


def bowling_runs(df: pd.DataFrame) -> pd.Series:
    extras = df.get("extras_type", pd.Series([""] * len(df), index=df.index)).astype(str).str.lower()
    extras_bowler = extras.str.contains("wides|noballs|no-balls|no ball", na=False)
    return pd.to_numeric(df.get("runs_batter", 0), errors="coerce").fillna(0) + pd.to_numeric(df.get("runs_extras", 0), errors="coerce").fillna(0).where(extras_bowler, 0)
