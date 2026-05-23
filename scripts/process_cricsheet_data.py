"""Parse real Cricsheet JSON zip files into analytical CSV tables."""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Any

import pandas as pd

from src.feature_engineering import BOWLER_WICKET_TYPES, classify_phase
from src.metrics import calculate_batter_summary, calculate_bowler_summary, calculate_matchups, phase_analysis, venue_analysis

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REGISTER_DIR = RAW_DIR / "register"


def _first_date(info: dict[str, Any]) -> str:
    dates = info.get("dates") or []
    if dates:
        return str(dates[0])
    return ""


def _team_players(info: dict[str, Any]) -> dict[str, str]:
    out = {}
    players = info.get("players") or {}
    if isinstance(players, dict):
        for team, names in players.items():
            for name in names or []:
                out[str(name)] = str(team)
    return out


def parse_match(data: dict[str, Any], match_id: str, source_file: str) -> list[dict[str, Any]]:
    info = data.get("info") or {}
    registry = ((info.get("registry") or {}).get("people") or {})
    teams = list(map(str, info.get("teams") or []))
    player_team = _team_players(info)
    match_type = str(info.get("match_type", "")).lower()
    gender = str(info.get("gender", "")).lower()
    event = info.get("event") or {}
    competition = event.get("name", "") if isinstance(event, dict) else str(event or "")
    date = _first_date(info)
    try:
        year = int(str(date)[:4]) if date else None
    except Exception:
        year = None
    venue = str(info.get("venue", "") or "")
    city = str(info.get("city", "") or "")
    rows = []
    innings_list = data.get("innings") or []
    for inn_idx, innings_obj in enumerate(innings_list, start=1):
        batting_team = str(innings_obj.get("team", "") or "")
        bowling_team = ""
        for t in teams:
            if t != batting_team:
                bowling_team = t
                break
        overs = innings_obj.get("overs") or []
        for over_obj in overs:
            over_num = over_obj.get("over")
            deliveries = over_obj.get("deliveries") or []
            legal_ball_in_over = 0
            for raw_ball_idx, delivery in enumerate(deliveries, start=1):
                batter = str(delivery.get("batter", "") or "")
                bowler = str(delivery.get("bowler", "") or "")
                non_striker = str(delivery.get("non_striker", "") or "")
                runs = delivery.get("runs") or {}
                extras = delivery.get("extras") or {}
                extras_types = ";".join(sorted(map(str, extras.keys()))) if isinstance(extras, dict) else ""
                is_legal = not any(x in extras_types.lower() for x in ["wides", "noballs", "no ball", "no-balls"])
                if is_legal:
                    legal_ball_in_over += 1
                wickets = delivery.get("wickets") or []
                wicket_type = ""
                player_out = ""
                fielders = ""
                if wickets:
                    wicket = wickets[0]
                    wicket_type = str(wicket.get("kind", "") or "")
                    player_out = str(wicket.get("player_out", "") or "")
                    fielder_objs = wicket.get("fielders") or []
                    names = []
                    for f in fielder_objs:
                        if isinstance(f, dict):
                            names.append(str(f.get("name", "")))
                        else:
                            names.append(str(f))
                    fielders = ";".join([n for n in names if n])
                # sometimes substitute team can make bowling team inference imperfect; keep best available.
                if batter in player_team:
                    batting_team = player_team[batter]
                    bowling_team = next((t for t in teams if t != batting_team), bowling_team)
                rows.append(
                    {
                        "match_id": match_id,
                        "source_file": source_file,
                        "date": date,
                        "year": year,
                        "match_type": match_type,
                        "gender": gender,
                        "competition": competition,
                        "venue": venue,
                        "city": city,
                        "innings": inn_idx,
                        "batting_team": batting_team,
                        "bowling_team": bowling_team,
                        "over": over_num,
                        "ball": legal_ball_in_over if is_legal else raw_ball_idx,
                        "raw_ball_number": raw_ball_idx,
                        "phase": classify_phase(over_num, match_type),
                        "batter": batter,
                        "bowler": bowler,
                        "non_striker": non_striker,
                        "batter_id": registry.get(batter, ""),
                        "bowler_id": registry.get(bowler, ""),
                        "non_striker_id": registry.get(non_striker, ""),
                        "runs_batter": int(runs.get("batter", 0) or 0),
                        "runs_extras": int(runs.get("extras", 0) or 0),
                        "runs_total": int(runs.get("total", 0) or 0),
                        "extras_type": extras_types,
                        "legal_ball": bool(is_legal),
                        "wicket_type": wicket_type,
                        "player_out": player_out,
                        "fielders": fielders,
                        "is_wicket": bool(player_out),
                        "is_bowler_wicket": wicket_type.lower() in BOWLER_WICKET_TYPES,
                        "is_dot": int((runs.get("total", 0) or 0) == 0),
                        "is_boundary": int((runs.get("batter", 0) or 0) in [4, 6]),
                    }
                )
    return rows


def iter_json_from_zip(zip_path: Path, limit: int | None = None):
    with zipfile.ZipFile(zip_path) as zf:
        names = [n for n in zf.namelist() if n.endswith(".json")]
        if limit:
            names = names[:limit]
        for name in names:
            with zf.open(name) as f:
                yield name, json.load(f)


def load_register_people() -> pd.DataFrame:
    path = REGISTER_DIR / "people.csv"
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def build_player_metadata(deliveries: pd.DataFrame) -> pd.DataFrame:
    people = load_register_people()
    players = set()
    for col in ["batter", "bowler", "non_striker"]:
        if col in deliveries.columns:
            players.update(deliveries[col].dropna().astype(str).tolist())
    meta = pd.DataFrame({"player": sorted(players)})
    if people.empty:
        meta["cricsheet_id"] = ""
        meta["unique_name"] = ""
    else:
        key_col = "name" if "name" in people.columns else None
        if key_col:
            rename = {"identifier": "cricsheet_id", "unique_name": "unique_name", key_col: "player"}
            cols = [c for c in [key_col, "identifier", "unique_name", "key_cricinfo", "key_bcci", "key_bigbash"] if c in people.columns]
            meta = meta.merge(people[cols].rename(columns=rename), on="player", how="left")
    # Do not invent batting hand, bowling style, or role. User can enrich this manually later.
    for col in ["batting_hand", "bowling_style", "role"]:
        if col not in meta.columns:
            meta[col] = "Data not available"
    return meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", action="append", dest="zips", help="Specific Cricsheet JSON zip(s). Defaults to data/raw/*_json.zip")
    parser.add_argument("--limit", type=int, default=None, help="Limit matches per zip for quick testing")
    parser.add_argument("--gender", choices=["male", "female", "all"], default="male")
    args = parser.parse_args(argv)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    zip_paths = [Path(z) for z in args.zips] if args.zips else sorted(RAW_DIR.glob("*_json.zip"))
    if not zip_paths:
        raise SystemExit("No Cricsheet JSON zip files found. Run python scripts/download_cricsheet_data.py first.")
    rows = []
    for zip_path in zip_paths:
        print(f"Processing {zip_path}")
        for name, data in iter_json_from_zip(zip_path, limit=args.limit):
            info = data.get("info") or {}
            if args.gender != "all" and str(info.get("gender", "")).lower() != args.gender:
                continue
            match_id = Path(name).stem
            rows.extend(parse_match(data, match_id=match_id, source_file=zip_path.name))
    if not rows:
        raise SystemExit("No deliveries parsed. Check --gender or zip contents.")
    deliveries = pd.DataFrame(rows)
    deliveries.to_csv(PROCESSED_DIR / "deliveries.csv", index=False)
    # compatibility aliases for older project names
    deliveries.to_csv(PROCESSED_DIR / "ball_by_ball.csv", index=False)
    calculate_batter_summary(deliveries).to_csv(PROCESSED_DIR / "batting_player_summary.csv", index=False)
    calculate_batter_summary(deliveries).to_csv(PROCESSED_DIR / "batter_summary.csv", index=False)
    calculate_bowler_summary(deliveries).to_csv(PROCESSED_DIR / "bowling_player_summary.csv", index=False)
    calculate_bowler_summary(deliveries).to_csv(PROCESSED_DIR / "bowler_summary.csv", index=False)
    calculate_matchups(deliveries).to_csv(PROCESSED_DIR / "batter_vs_bowler_matchups.csv", index=False)
    phase_analysis(deliveries).to_csv(PROCESSED_DIR / "phase_analysis.csv", index=False)
    venue_analysis(deliveries).to_csv(PROCESSED_DIR / "venue_analysis.csv", index=False)
    build_player_metadata(deliveries).to_csv(PROCESSED_DIR / "player_metadata.csv", index=False)
    image_map = PROCESSED_DIR / "player_image_map.csv"
    if not image_map.exists():
        pd.DataFrame(columns=["player", "image_url", "image_source", "credit", "country_or_team"]).to_csv(image_map, index=False)
    print(f"Created processed files in {PROCESSED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
