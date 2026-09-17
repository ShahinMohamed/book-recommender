import argparse
import json
from pathlib import Path

import numpy as np

from app.recommenders.dataset import load_books
from app.recommenders.semantic import MODEL_NAME, fingerprint

PREFERRED_TITLES = (
    "the hobbit",
    "harry potter",
    "the hunger games",
    "pride and prejudice",
    "jane eyre",
    "the great gatsby",
    "dune",
    "foundation",
    "little women",
    "the handmaid's tale",
)


def generate(args: argparse.Namespace) -> None:
    frame = load_books(args.dataset)
    embeddings = np.load(args.source_embeddings, mmap_mode="r")
    if embeddings.shape != (len(frame), 384):
        raise ValueError("Source embeddings do not match the cleaned dataset")

    normalized_titles = frame["Title"].str.casefold()
    preferred = frame.index[
        normalized_titles.map(lambda title: any(needle in title for needle in PREFERRED_TITLES))
    ].tolist()
    eligible = frame.index[
        frame["Description"].notna() & frame["Category"].notna() & frame["Authors"].notna()
    ].to_numpy()
    rng = np.random.default_rng(args.seed)
    sampled = rng.choice(eligible, size=args.books, replace=False).tolist()
    selected = list(dict.fromkeys(preferred + sampled))[: args.books]
    selected.sort()

    demo = frame.iloc[selected].reset_index(drop=True)
    demo_embeddings = np.asarray(embeddings[selected], dtype=np.float32)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    demo.to_csv(args.output_dir / "demo_books.csv", index=False)
    np.save(args.output_dir / "demo_embeddings.npy", demo_embeddings)
    (args.output_dir / "demo_embeddings_metadata.json").write_text(
        json.dumps(
            {
                "model_name": MODEL_NAME,
                "semantic_fingerprint": fingerprint(demo),
                "number_of_books": len(demo),
                "dimensions": 384,
                "source": "elvinrustam/books-dataset (CC0), deterministic subset",
                "seed": args.seed,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Created a {len(demo)}-book demo catalog in {args.output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the small CC0 catalog bundled for Docker quick start"
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--source-embeddings", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--books", type=int, default=600)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


if __name__ == "__main__":
    generate(parse_args())
