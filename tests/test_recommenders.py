import pandas as pd

from app.recommenders.tfidf import WeightedTfidfBaseline
from app.repositories.books import _rating_weight


def test_rating_weight_preserves_dislikes_as_exclusions():
    assert [_rating_weight(value) for value in range(1, 6)] == [0.0, 0.0, 1.0, 2.0, 3.0]


def test_offline_tfidf_can_rank_similar_books():
    frame = pd.DataFrame(
        {
            "Title": ["Forest Magic", "Forest Spell", "Database Systems"],
            "Authors": ["A. Writer", "B. Writer", "C. Engineer"],
            "Category": ["Fantasy", "Fantasy", "Technology"],
            "Description": [
                "A magical forest adventure",
                "An enchanted forest journey",
                "PostgreSQL query design",
            ],
        }
    )
    recommender = WeightedTfidfBaseline().fit(frame)
    ranked, _ = recommender.recommend_indices(0, number_of_books=1)
    assert ranked.tolist() == [1]
