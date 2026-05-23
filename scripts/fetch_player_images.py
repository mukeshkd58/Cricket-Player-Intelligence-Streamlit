"""Fetch real open-source player image URLs from Wikidata/Wikimedia Commons.

This script does NOT scrape Google Images and does NOT create fake faces.
It stores image URLs + attribution metadata in data/processed/player_image_map.csv.
"""
from __future__ import annotations

import argparse
import html
import re
import time
from dataclasses import dataclass
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests

from src.data_loader import BATTER_SUMMARY_PATH, BOWLER_SUMMARY_PATH, PLAYER_IMAGE_MAP_PATH, PROCESSED_DIR

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "CricketPlayerIntelligence/1.0 (Wikidata/Wikimedia image map; educational portfolio project)"
IMAGE_COLUMNS = ["player", "image_url", "image_source", "credit", "country_or_team"]


@dataclass
class ImageResult:
    player: str
    image_url: str
    image_source: str
    credit: str
    country_or_team: str = ""


def clean_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def read_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def top_players(n_batters: int, n_bowlers: int) -> list[str]:
    players: list[str] = []
    b = read_csv(BATTER_SUMMARY_PATH)
    if not b.empty and "batter" in b.columns:
        col = "runs" if "runs" in b.columns else b.columns[0]
        players.extend(b.sort_values(col, ascending=False)["batter"].dropna().astype(str).head(n_batters).tolist())
    bw = read_csv(BOWLER_SUMMARY_PATH)
    if not bw.empty and "bowler" in bw.columns:
        col = "wickets" if "wickets" in bw.columns else bw.columns[0]
        players.extend(bw.sort_values(col, ascending=False)["bowler"].dropna().astype(str).head(n_bowlers).tolist())
    seen, out = set(), []
    for p in players:
        key = p.casefold().strip()
        if key and key not in seen:
            out.append(p); seen.add(key)
    return out


def wikidata_search(player: str) -> list[dict[str, Any]]:
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": f"{player} cricketer",
        "limit": 5,
    }
    r = requests.get(WIKIDATA_API, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    return r.json().get("search", [])


def wikidata_entity(qid: str) -> dict[str, Any]:
    params = {"action": "wbgetentities", "ids": qid, "format": "json", "props": "claims|descriptions|labels"}
    r = requests.get(WIKIDATA_API, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    return r.json().get("entities", {}).get(qid, {})


def commons_image_info(filename: str) -> tuple[str, str]:
    title = "File:" + filename.replace(" ", "_")
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 450,
    }
    r = requests.get(COMMONS_API, params=params, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if infos:
            info = infos[0]
            url = info.get("thumburl") or info.get("url") or f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(filename)}"
            ext = info.get("extmetadata") or {}
            artist = clean_text((ext.get("Artist") or {}).get("value", ""))
            license_short = clean_text((ext.get("LicenseShortName") or {}).get("value", ""))
            credit = clean_text((ext.get("Credit") or {}).get("value", ""))
            bits = [b for b in [artist, license_short, credit] if b]
            return url, " | ".join(bits)[:500]
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(filename)}", "Review Wikimedia Commons metadata"


def fetch_image(player: str) -> ImageResult | None:
    try:
        for item in wikidata_search(player):
            qid = item.get("id")
            desc = (item.get("description") or "").lower()
            if qid is None:
                continue
            entity = wikidata_entity(qid)
            edesc = " ".join(d.get("value", "") for d in (entity.get("descriptions") or {}).values()).lower()
            if "cricket" not in desc and "cricket" not in edesc and "cricketer" not in desc + edesc:
                continue
            claims = entity.get("claims") or {}
            p18 = claims.get("P18") or []
            if not p18:
                continue
            filename = p18[0].get("mainsnak", {}).get("datavalue", {}).get("value")
            if not filename:
                continue
            url, credit = commons_image_info(filename)
            return ImageResult(player=player, image_url=url, image_source=f"Wikidata {qid} / Wikimedia Commons", credit=credit)
    except Exception as exc:
        print(f"Warning: image lookup failed for {player}: {exc}")
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-batters", type=int, default=40)
    parser.add_argument("--top-bowlers", type=int, default=40)
    parser.add_argument("--players", nargs="*", help="Specific players to fetch instead of automatic top players")
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between API lookups")
    args = parser.parse_args(argv)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    existing = read_csv(PLAYER_IMAGE_MAP_PATH)
    if existing.empty:
        existing = pd.DataFrame(columns=IMAGE_COLUMNS)
    existing_keys = set(existing.get("player", pd.Series(dtype=str)).dropna().astype(str).str.casefold())
    players = args.players if args.players else top_players(args.top_batters, args.top_bowlers)
    results = []
    for p in players:
        if p.casefold() in existing_keys:
            print(f"Skip existing: {p}"); continue
        print(f"Searching image: {p}")
        res = fetch_image(p)
        if res:
            print(f"  Found: {res.image_url}")
            results.append(res.__dict__)
        else:
            print("  No Commons image found; fallback avatar will be used.")
        time.sleep(args.sleep)
    if results:
        updated = pd.concat([existing, pd.DataFrame(results)], ignore_index=True)
    else:
        updated = existing
    updated = updated.reindex(columns=IMAGE_COLUMNS)
    updated.to_csv(PLAYER_IMAGE_MAP_PATH, index=False)
    assets_path = Path(__file__).resolve().parents[1] / "assets" / "player_images" / "player_image_map.csv"
    assets_path.parent.mkdir(parents=True, exist_ok=True)
    if not assets_path.exists():
        updated.head(0).to_csv(assets_path, index=False)
    print(f"Image map saved to {PLAYER_IMAGE_MAP_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
