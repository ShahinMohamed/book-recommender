"""Weighted TF-IDF recommender kept outside the FastAPI request path.

The web application uses only semantic pgvector recommendations. This module
remains available for offline use and is not imported by the running app.
"""

from math import sqrt

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_COLUMN_WEIGHTS = {
    "Category": 4.0,
    "Authors": 3.0,
    "Title": 2.0,
    "Description": 1.0,
}


class WeightedTfidfBaseline:
    def __init__(self, column_weights: dict[str, float] | None = None) -> None:
        self.column_weights = column_weights or DEFAULT_COLUMN_WEIGHTS
        self.vectorizers: dict[str, TfidfVectorizer] = {}
        self.matrix: csr_matrix | None = None

    def fit(self, frame: pd.DataFrame) -> "WeightedTfidfBaseline":
        feature_matrices = []
        for column, weight in self.column_weights.items():
            vectorizer = TfidfVectorizer(
                stop_words="english",
                min_df=2,
                ngram_range=(1, 2),
                max_features=25_000,
            )
            matrix = vectorizer.fit_transform(frame[column].fillna("").astype(str))
            # sqrt(weight) preserves the original weighted cosine behavior.
            feature_matrices.append(matrix * sqrt(weight))
            self.vectorizers[column] = vectorizer
        self.matrix = hstack(feature_matrices).tocsr()
        return self

    def similarities(self, indices: list[int] | np.ndarray) -> np.ndarray:
        if self.matrix is None:
            raise RuntimeError("Fit the TF-IDF baseline before requesting similarities")
        return cosine_similarity(self.matrix[indices], self.matrix)

    def recommend_indices(self, index: int, number_of_books: int = 5) -> tuple[np.ndarray, np.ndarray]:
        scores = self.similarities([index])[0]
        scores[index] = -np.inf
        ranked = scores.argsort()[::-1][:number_of_books]
        return ranked, scores[ranked]
