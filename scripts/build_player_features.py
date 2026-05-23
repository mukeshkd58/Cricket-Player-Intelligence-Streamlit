"""Rebuild player-level analytical tables from processed real deliveries."""
from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import pandas as pd

from src.data_loader import DELIVERIES_PATH, PROCESSED_DIR
from src.metrics import calculate_batter_summary, calculate_bowler_summary, calculate_matchups, phase_analysis, venue_analysis


def main() -> int:
    if not DELIVERIES_PATH.exists():
        raise SystemExit("Missing data/processed/deliveries.csv. Run scripts/process_cricsheet_data.py first.")
    df = pd.read_csv(DELIVERIES_PATH)
    calculate_batter_summary(df).to_csv(PROCESSED_DIR / "batting_player_summary.csv", index=False)
    calculate_bowler_summary(df).to_csv(PROCESSED_DIR / "bowling_player_summary.csv", index=False)
    calculate_matchups(df).to_csv(PROCESSED_DIR / "batter_vs_bowler_matchups.csv", index=False)
    phase_analysis(df).to_csv(PROCESSED_DIR / "phase_analysis.csv", index=False)
    venue_analysis(df).to_csv(PROCESSED_DIR / "venue_analysis.csv", index=False)
    print("Player features rebuilt from real processed deliveries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
