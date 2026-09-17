from dataclasses import dataclass
from uuid import UUID

import numpy as np
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, contains_eager

from app.models import Book, Rating


@dataclass(frozen=True)
class Recommendation:
    book: Book
    score: float | None


def get_book(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)


def search_books(db: Session, query: str, limit: int = 8) -> list[Book]:
    cleaned = " ".join(query.split())[:120]
    if len(cleaned) < 2:
        return []

    escaped = cleaned.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    prefix = f"{escaped}%"
    ordering = case(
        (func.lower(Book.title) == cleaned.casefold(), 0),
        (Book.title.ilike(prefix, escape="\\"), 1),
        else_=2,
    )
    return list(
        db.scalars(
            select(Book)
            .where(Book.title.ilike(pattern, escape="\\"))
            .order_by(ordering, Book.title)
            .limit(limit)
        )
    )


def get_book_rating(db: Session, book_id: int, reader_id: UUID) -> Rating | None:
    return db.scalar(select(Rating).where(Rating.book_id == book_id, Rating.reader_id == reader_id))


def count_read_books(db: Session, reader_id: UUID) -> int:
    return int(db.scalar(select(func.count(Rating.id)).where(Rating.reader_id == reader_id)) or 0)


def get_read_books(db: Session, reader_id: UUID, page: int, page_size: int = 18) -> tuple[list[Book], int]:
    total = count_read_books(db, reader_id)
    items = list(
        db.scalars(
            select(Book)
            .join(Rating, Rating.book_id == Book.id)
            .where(Rating.reader_id == reader_id)
            .options(contains_eager(Book.ratings))
            .order_by(Rating.updated_at.desc(), Book.title)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).unique()
    )
    return items, total


def _rating_weight(value: int) -> float:
    return {3: 1.0, 4: 2.0, 5: 3.0}.get(value, 0.0)


def _discovery_recommendations(db: Session, limit: int) -> list[Recommendation]:
    candidates = list(
        db.scalars(
            select(Book)
            .where(Book.description.is_not(None), Book.category.is_not(None))
            .order_by(Book.publish_year.desc().nullslast(), Book.dataset_index)
            .limit(max(80, limit * 8))
        )
    )
    results: list[Recommendation] = []
    deferred: list[Recommendation] = []
    seen_categories: set[str] = set()
    for book in candidates:
        category = (book.category or "Uncategorized").split(",", 1)[0].strip().casefold()
        if category in seen_categories:
            deferred.append(Recommendation(book=book, score=None))
            continue
        seen_categories.add(category)
        results.append(Recommendation(book=book, score=None))
        if len(results) == limit:
            break
    if len(results) < limit:
        results.extend(deferred[: limit - len(results)])
    return results


def get_content_recommendations(
    db: Session, reader_id: UUID, limit: int = 12
) -> tuple[list[Recommendation], bool]:
    rated_rows = db.execute(
        select(Book.id, Book.embedding, Rating.value).join(Rating).where(Rating.reader_id == reader_id)
    ).all()
    liked = [(row.embedding, _rating_weight(row.value)) for row in rated_rows if row.value >= 3]
    if not liked:
        return _discovery_recommendations(db, limit), False

    vectors = np.asarray([item[0] for item in liked], dtype=np.float32)
    weights = np.asarray([item[1] for item in liked], dtype=np.float32)
    profile = np.average(vectors, axis=0, weights=weights)
    norm = float(np.linalg.norm(profile))
    if norm == 0:
        return _discovery_recommendations(db, limit), False
    profile = (profile / norm).tolist()

    excluded_ids = [row.id for row in rated_rows]
    distance = Book.embedding.cosine_distance(profile)
    score = (1 - distance).label("score")
    rows = db.execute(
        select(Book, score).where(Book.id.not_in(excluded_ids)).order_by(distance).limit(limit)
    ).all()
    return [Recommendation(book=row.Book, score=float(row.score)) for row in rows], True


def get_recommendations(db: Session, reader_id: UUID, limit: int = 12) -> tuple[list[Recommendation], bool]:
    """Backward-compatible name for the content-based production engine."""
    return get_content_recommendations(db, reader_id, limit)
