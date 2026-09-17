import argparse
from pathlib import Path

from app.recommenders.dataset import load_books
from app.recommenders.semantic import load_or_create_embeddings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate verified semantic embedding artifacts")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, default=Path("artifacts/semantic_embeddings.npy"))
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("artifacts/semantic_embeddings_metadata.json"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    books = load_books(args.dataset)
    embeddings = load_or_create_embeddings(books, args.embeddings, args.metadata)
    print(f"Ready: {len(books):,} books × {embeddings.shape[1]} dimensions")
