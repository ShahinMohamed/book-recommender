import argparse
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psycopg
from pgvector.psycopg import register_vector

from app.recommenders.dataset import load_books
from app.recommenders.semantic import load_or_create_embeddings

UPSERT_SQL = """
INSERT INTO books (
    dataset_index, title, authors, description, category, publisher,
    price, publish_month, publish_year, embedding
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (dataset_index) DO UPDATE SET
    title = EXCLUDED.title,
    authors = EXCLUDED.authors,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    publisher = EXCLUDED.publisher,
    price = EXCLUDED.price,
    publish_month = EXCLUDED.publish_month,
    publish_year = EXCLUDED.publish_year,
    embedding = EXCLUDED.embedding,
    updated_at = NOW()
"""


def _nullable(value: Any) -> Any:
    return None if pd.isna(value) else value


def _row(index: int, item: pd.Series, embedding: np.ndarray) -> tuple[Any, ...]:
    price = _nullable(item["Price Starting With ($)"])
    year = _nullable(item["Publish Date (Year)"])
    return (
        int(item["Dataset Index"]),
        str(item["Title"]),
        _nullable(item["Authors"]),
        _nullable(item["Description"]),
        _nullable(item["Category"]),
        _nullable(item["Publisher"]),
        Decimal(str(price)).quantize(Decimal("0.01")) if price is not None else None,
        _nullable(item["Publish Date (Month)"]),
        int(year) if year is not None else None,
        embedding,
    )


def run(args: argparse.Namespace) -> None:
    frame = load_books(args.dataset, limit=args.limit)
    embeddings = load_or_create_embeddings(frame, args.embeddings, args.metadata)
    if embeddings.shape != (len(frame), 384):
        raise ValueError(f"Expected {(len(frame), 384)} embeddings, received {embeddings.shape}")

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://book_recommender:book_recommender@localhost:5432/book_recommender",
    ).replace("postgresql+psycopg://", "postgresql://", 1)
    with psycopg.connect(database_url) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            for start in range(0, len(frame), args.batch_size):
                stop = min(start + args.batch_size, len(frame))
                values = [_row(index, frame.iloc[index], embeddings[index]) for index in range(start, stop)]
                cursor.executemany(UPSERT_SQL, values)
                connection.commit()
                print(f"Ingested {stop:,} / {len(frame):,} books", flush=True)
        with connection.cursor() as cursor:
            cursor.execute("ANALYZE books")
        connection.commit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the books dataset and semantic vectors into PostgreSQL"
    )
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--embeddings", type=Path, default=Path("artifacts/semantic_embeddings.npy"))
    parser.add_argument("--metadata", type=Path, default=Path("artifacts/semantic_embeddings_metadata.json"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=500)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
