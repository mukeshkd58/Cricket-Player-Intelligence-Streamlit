"""Download real Cricsheet JSON zip files and Cricsheet Register CSV files.

Default command:
    python scripts/download_cricsheet_data.py

This downloads international Test/ODI/T20I JSON zip files plus Cricsheet Register
people.csv and names.csv. Use --preset to add IPL/BBL/PSL etc.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REGISTER_DIR = RAW_DIR / "register"

PRESET_URLS = {
    "tests_json": "https://cricsheet.org/downloads/tests_json.zip",
    "odis_json": "https://cricsheet.org/downloads/odis_json.zip",
    "t20s_json": "https://cricsheet.org/downloads/t20s_json.zip",
    "ipl_json": "https://cricsheet.org/downloads/ipl_json.zip",
    "bbl_json": "https://cricsheet.org/downloads/bbl_json.zip",
    "psl_json": "https://cricsheet.org/downloads/psl_json.zip",
    "cpl_json": "https://cricsheet.org/downloads/cpl_json.zip",
    "hundred_json": "https://cricsheet.org/downloads/the_hundred_json.zip",
}
REGISTER_URLS = {
    "people.csv": "https://cricsheet.org/register/people.csv",
    "names.csv": "https://cricsheet.org/register/names.csv",
}
USER_AGENT = "CricketPlayerIntelligence/1.0 (educational portfolio project)"


def download(url: str, output: Path, overwrite: bool = False) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not overwrite:
        print(f"Already exists: {output}")
        return
    print(f"Downloading {url}")
    with requests.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=60) as r:
        if r.status_code == 404:
            raise RuntimeError(f"Not found: {url}. Check Cricsheet downloads page for the exact competition code.")
        r.raise_for_status()
        with output.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 512):
                if chunk:
                    f.write(chunk)
    print(f"Saved: {output} ({output.stat().st_size/1024/1024:.1f} MB)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", nargs="*", default=["tests_json", "odis_json", "t20s_json"], choices=sorted(PRESET_URLS), help="Cricsheet zip presets to download")
    parser.add_argument("--url", action="append", help="Custom Cricsheet zip URL. Can be provided more than once.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for preset in args.preset:
        url = PRESET_URLS[preset]
        download(url, RAW_DIR / f"{preset}.zip", overwrite=args.overwrite)
    if args.url:
        for url in args.url:
            name = url.rstrip("/").split("/")[-1] or "custom_cricsheet.zip"
            download(url, RAW_DIR / name, overwrite=args.overwrite)
    for filename, url in REGISTER_URLS.items():
        try:
            download(url, REGISTER_DIR / filename, overwrite=args.overwrite)
        except Exception as exc:
            print(f"Warning: register download failed for {filename}: {exc}", file=sys.stderr)
    print("Download step completed. Next: python scripts/process_cricsheet_data.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
