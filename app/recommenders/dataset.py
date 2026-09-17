import os
from pathlib import Path

import pandas as pd

DATASET_HANDLE = "elvinrustam/books-dataset"
DATASET_FILENAME = "BooksDatasetClean.csv"
DATASET_COLUMNS = [
    "Title",
    "Authors",
    "Description",
    "Category",
    "Publisher",
    "Price Starting With ($)",
    "Publish Date (Month)",
    "Publish Date (Year)",
]


def resolve_dataset_path(explicit_path: str | Path | None = None) -> Path:
    candidates = [
        Path(explicit_path).expanduser() if explicit_path else None,
        Path(os.environ["DATASET_PATH"]).expanduser() if os.environ.get("DATASET_PATH") else None,
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate

    import kagglehub

    dataset_dir = Path(kagglehub.dataset_download(DATASET_HANDLE))
    csv_path = dataset_dir / DATASET_FILENAME
    if not csv_path.exists():
        available = sorted(path.name for path in dataset_dir.glob("*.csv"))
        raise FileNotFoundError(f"Could not find {DATASET_FILENAME}. Available CSV files: {available}")
    return csv_path


def load_books(explicit_path: str | Path | None = None, limit: int | None = None) -> pd.DataFrame:
    csv_path = resolve_dataset_path(explicit_path)
    frame = pd.read_csv(csv_path)
    missing_columns = set(DATASET_COLUMNS).difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing_columns)}")
    source_indices = frame.get("Dataset Index")
    frame = frame[DATASET_COLUMNS].copy()
    if source_indices is not None:
        frame["Dataset Index"] = source_indices
    frame = frame.dropna(subset=["Title"]).copy()
    frame["Title"] = frame["Title"].astype(str).str.strip()
    frame = frame[frame["Title"] != ""]
    frame = frame.drop_duplicates(subset=["Title"]).reset_index(drop=True)
    if "Dataset Index" not in frame:
        frame["Dataset Index"] = frame.index
    frame["Dataset Index"] = frame["Dataset Index"].astype(int)
    if limit is not None:
        frame = frame.head(limit).copy()
    return frame


def semantic_text(frame: pd.DataFrame) -> pd.Series:
    return (
        "Title: "
        + frame["Title"].fillna("").astype(str)
        + ". Author: "
        + frame["Authors"].fillna("").astype(str)
        + ". Category: "
        + frame["Category"].fillna("").astype(str)
        + ". Description: "
        + frame["Description"].fillna("").astype(str)
    )
