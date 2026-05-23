# Reproducibility Checklist

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_cricsheet_data.py
python scripts/process_cricsheet_data.py --limit 50 --gender male
python scripts/build_player_features.py
python scripts/fetch_player_images.py --top-batters 20 --top-bowlers 20
python scripts/train_models.py
streamlit run app.py
```

Check:

- `data/processed/deliveries.csv` exists
- player summaries exist
- Streamlit pages open without crashing
- missing images show fallback avatars
- ML page handles missing/trained models
- PDF export creates a file under `outputs/reports/`
