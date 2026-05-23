from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.data_loader import DELIVERIES_PATH, resolve_data_path, sample_path_for
from src.model_utils import train_all_models


def main() -> int:
    data_path = resolve_data_path(DELIVERIES_PATH)
    if not data_path.exists():
        raise SystemExit(
            "Missing delivery data. Run scripts/process_cricsheet_data.py for full data "
            f"or keep {sample_path_for(DELIVERIES_PATH)} for sample-mode training."
        )
    if data_path.name.endswith("_sample.csv"):
        print(f"Training from real sample data: {data_path}")
    else:
        print(f"Training from full processed data: {data_path}")
    df = pd.read_csv(data_path)
    metrics = train_all_models(df)
    for m in metrics:
        print(m)
    print("Model training step completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
