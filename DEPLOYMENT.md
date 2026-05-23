# Deployment Guide

This guide prepares the project for GitHub and Streamlit Community Cloud.

## 1. Confirm the entrypoint

Streamlit main file:

```text
app.py
```

## 2. Clean files before commit

Do not commit local/cache/generated files:

```bash
# macOS/Linux/Git Bash
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
rm -rf outputs/
rm -rf .venv/ venv/
rm -f .env
rm -f data/raw/*.zip
rm -f data/raw/*.json
rm -f data/raw/register/*.csv
rm -f data/processed/deliveries.csv
rm -f data/processed/ball_by_ball.csv
```

Keep these placeholders:

```text
data/raw/.gitkeep
data/processed/.gitkeep
data/images/.gitkeep
models/.gitkeep
```

## 3. Large data policy

The full files below are too large for normal GitHub repository commits:

```text
data/processed/deliveries.csv      ~921MB
data/processed/ball_by_ball.csv    ~921MB
```

They are intentionally excluded by `.gitignore`.

The repository includes real sample files under:

```text
data/sample/
```

The app automatically falls back to these sample files when full processed files are missing.

## 4. Local run

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

## 5. Reproduce full data locally

```bash
python scripts/download_cricsheet_data.py
python scripts/process_cricsheet_data.py
python scripts/build_player_features.py
python scripts/fetch_player_images.py
python scripts/train_models.py
streamlit run app.py
```

## 6. Upload to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Cricket Player Intelligence Streamlit app"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

## 7. Deploy on Streamlit Community Cloud

1. Open Streamlit Community Cloud.
2. Create a new app.
3. Select the GitHub repository.
4. Select the branch, usually `main`.
5. Set **Main file path** to `app.py`.
6. Deploy.
7. Confirm the app reports sample data mode in the dashboard if full data is not present.

## 8. Full dataset options

For the full processed data, use one of these approaches:

### Option A: Regenerate locally

Recommended for a portfolio repository. Keep GitHub lightweight and reproducible.

### Option B: Git LFS

Use Git LFS only if you understand storage and bandwidth limits:

```bash
git lfs install
git lfs track "data/processed/*.csv"
git add .gitattributes data/processed/deliveries.csv data/processed/ball_by_ball.csv
git commit -m "Track full processed data with Git LFS"
```

### Option C: External storage

Store full processed data in a private object store or release asset, then download it locally before running. Do not commit secrets or access keys to GitHub.

## 9. Streamlit secrets

Do not commit secrets. Use Streamlit Cloud's secrets management for any future private credentials.

Ignored local files include:

```text
.env
.streamlit/secrets.toml
```
