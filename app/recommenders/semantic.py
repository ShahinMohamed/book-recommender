import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.recommenders.dataset import semantic_text

MODEL_NAME = "all-MiniLM-L6-v2"


def fingerprint(frame: pd.DataFrame) -> str:
    return hashlib.sha256("\n".join(semantic_text(frame)).encode("utf-8")).hexdigest()


def load_or_create_embeddings(
    frame: pd.DataFrame,
    embeddings_path: str | Path,
    metadata_path: str | Path,
    model_name: str = MODEL_NAME,
) -> np.ndarray:
    embeddings_file = Path(embeddings_path)
    metadata_file = Path(metadata_path)
    expected_fingerprint = fingerprint(frame)

    if embeddings_file.exists() and metadata_file.exists():
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        embeddings = np.load(embeddings_file)
        if (
            metadata.get("model_name") == model_name
            and metadata.get("semantic_fingerprint") == expected_fingerprint
            and embeddings.shape == (len(frame), 384)
        ):
            return np.asarray(embeddings, dtype=np.float32)

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    embeddings = model.encode(
        semantic_text(frame).tolist(),
        show_progress_bar=True,
        normalize_embeddings=True,
    ).astype(np.float32)
    embeddings_file.parent.mkdir(parents=True, exist_ok=True)
    np.save(embeddings_file, embeddings)
    metadata_file.write_text(
        json.dumps(
            {
                "model_name": model_name,
                "semantic_fingerprint": expected_fingerprint,
                "number_of_books": len(frame),
                "dimensions": int(embeddings.shape[1]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return embeddings
