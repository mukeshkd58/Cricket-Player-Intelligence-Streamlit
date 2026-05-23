# Data Card

## Project

Cricket Player Strength & Weakness Intelligence Platform

## Data Type

Real cricket ball-by-ball and derived player analytics data.

## Sources

- Cricsheet ball-by-ball match JSON data
- Cricsheet Register for identity mapping where available
- Wikidata / Wikimedia Commons for optional player image metadata

## Synthetic Data Policy

No fake cricket records are created. No player statistics are invented. No fake screenshots are included.

If metadata is not available from the supported real sources, the app displays:

```text
Data not available
```

## Full Dataset Summary

The uploaded ZIP contained the following full processed data volumes:

| File / Table | Rows |
|---|---:|
| `deliveries.csv` | about 3,794,030 |
| `batting_player_summary.csv` | 4,884 batters |
| `bowling_player_summary.csv` | 3,672 bowlers |
| `batter_vs_bowler_matchups.csv` | 195,450 matchups |
| `phase_analysis.csv` | 20,931 |
| `venue_analysis.csv` | 83,059 |
| `player_metadata.csv` | 5,283 players |

## Included Repository Sample

The repository includes `data/sample/`, a compact real-row extract for cloud demo deployment.

These sample rows are selected from the original files and are not synthetic.

Primary sample files:

```text
data/sample/deliveries_sample.csv
data/sample/batting_player_summary_sample.csv
data/sample/bowling_player_summary_sample.csv
data/sample/batter_vs_bowler_matchups_sample.csv
data/sample/phase_analysis_sample.csv
data/sample/venue_analysis_sample.csv
data/sample/player_metadata_sample.csv
data/sample/player_image_map_sample.csv
```

## Excluded from GitHub

The following full files are excluded from normal GitHub commits because of size and repository hygiene:

```text
data/processed/deliveries.csv
data/processed/ball_by_ball.csv
data/raw/*.zip
```

The two full processed delivery files are about 921MB each in the ZIP and should not be committed to a normal GitHub repository.

## App Data Loading Behavior

The app uses the following data priority:

1. Full processed files in `data/processed/`
2. Real sample files in `data/sample/`
3. Empty state with reproduction instructions

This allows the same codebase to support both local full-data analysis and Streamlit Community Cloud demo deployment.

## Reproduction Commands

```bash
python scripts/download_cricsheet_data.py
python scripts/process_cricsheet_data.py
python scripts/build_player_features.py
python scripts/fetch_player_images.py
python scripts/train_models.py
```

## Known Data Limitations

Cricsheet ball-by-ball data does not always include:

- batting hand
- bowling style
- shot type
- line and length
- field placements
- pitch maps
- wagon wheels
- verified player images

The application does not infer or fabricate those fields.

## Example Real Records

| Example | Value |
|---|---|
| Top batter by runs | V Kohli — 27,778 runs, 35,056 balls, 529 matches, average 53.01, strike rate 79.24 |
| Top bowler by wickets | JM Anderson — 950 wickets, 8,044.3 overs, 377 matches, economy 3.22, average 27.25 |
| High-volume matchup | JE Root vs RA Jadeja — 1,456 balls, 736 runs, 14 dismissals |

## Ethical / Integrity Notes

- This is an analytics and portfolio project, not a betting product.
- ML predictions are risk signals, not final professional decisions.
- The app is transparent when data is missing or sample sizes are small.
