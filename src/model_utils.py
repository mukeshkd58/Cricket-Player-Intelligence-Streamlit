from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.data_loader import MODELS_DIR
from src.feature_engineering import add_derived_delivery_features

FEATURE_COLUMNS = ["batter", "bowler", "batting_team", "bowling_team", "match_type", "phase", "over", "innings"]
NUMERIC_COLS = ["over", "innings"]
CATEGORICAL_COLS = ["batter", "bowler", "batting_team", "bowling_team", "match_type", "phase"]


def _prepare_ml_frame(df: pd.DataFrame, target: str) -> tuple[pd.DataFrame, pd.Series]:
    df = add_derived_delivery_features(df)
    if df.empty:
        return pd.DataFrame(), pd.Series(dtype=int)
    if target == "batter_dismissal":
        y = (df.get("player_out", "").astype(str) == df.get("batter", "").astype(str)).astype(int)
    elif target == "boundary_probability":
        y = (pd.to_numeric(df.get("runs_batter", 0), errors="coerce").fillna(0).isin([4, 6])).astype(int)
    elif target == "bowler_wicket":
        y = df.get("is_bowler_wicket", 0).astype(int)
    else:
        raise ValueError(f"Unknown target: {target}")
    X = df.copy()
    for col in FEATURE_COLUMNS:
        if col not in X.columns:
            X[col] = "Unknown" if col in CATEGORICAL_COLS else 0
    X = X[FEATURE_COLUMNS]
    X[NUMERIC_COLS] = X[NUMERIC_COLS].apply(pd.to_numeric, errors="coerce").fillna(0)
    X[CATEGORICAL_COLS] = X[CATEGORICAL_COLS].fillna("Unknown").astype(str)
    return X, y


def _make_pipeline(model_type: str = "random_forest") -> Pipeline:
    pre = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=5), CATEGORICAL_COLS),
            ("num", StandardScaler(), NUMERIC_COLS),
        ]
    )
    if model_type == "logistic_regression":
        clf = LogisticRegression(max_iter=600, class_weight="balanced", n_jobs=None)
    else:
        clf = RandomForestClassifier(n_estimators=180, max_depth=14, min_samples_leaf=5, random_state=42, n_jobs=-1, class_weight="balanced_subsample")
    return Pipeline([("preprocess", pre), ("model", clf)])


def train_classifier(df: pd.DataFrame, target: str, model_type: str = "random_forest", min_rows: int = 500) -> dict[str, Any]:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    X, y = _prepare_ml_frame(df, target)
    if X.empty or len(X) < min_rows or y.nunique() < 2:
        return {"target": target, "status": "skipped", "reason": f"Need at least {min_rows} rows and two classes. Found rows={len(X)}, classes={int(y.nunique()) if len(y) else 0}."}
    stratify = y if y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.22, random_state=42, stratify=stratify)
    pipe = _make_pipeline(model_type)
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    proba = pipe.predict_proba(X_test)[:, 1] if hasattr(pipe[-1], "predict_proba") else pred
    metrics = {
        "target": target,
        "status": "trained",
        "model_type": model_type,
        "rows": int(len(X)),
        "positive_rate": float(y.mean()),
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, proba)) if len(np.unique(y_test)) > 1 else None,
    }
    path = MODELS_DIR / f"{target}_model.pkl"
    joblib.dump(pipe, path)
    (MODELS_DIR / f"{target}_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def train_all_models(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        train_classifier(df, "batter_dismissal"),
        train_classifier(df, "boundary_probability"),
        train_classifier(df, "bowler_wicket"),
    ]


def load_model(target: str):
    path = MODELS_DIR / f"{target}_model.pkl"
    if not path.exists():
        return None
    return joblib.load(path)


def load_metrics(target: str) -> dict[str, Any]:
    path = MODELS_DIR / f"{target}_metrics.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def predict_probability(target: str, row: dict[str, Any]) -> float | None:
    model = load_model(target)
    if model is None:
        return None
    X = pd.DataFrame([{col: row.get(col, "Unknown") for col in FEATURE_COLUMNS}])
    X[NUMERIC_COLS] = X[NUMERIC_COLS].apply(pd.to_numeric, errors="coerce").fillna(0)
    X[CATEGORICAL_COLS] = X[CATEGORICAL_COLS].fillna("Unknown").astype(str)
    return float(model.predict_proba(X)[:, 1][0])
