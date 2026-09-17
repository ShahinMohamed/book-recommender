from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Book, Rating


class UnknownBookError(ValueError):
    pass


def save_rating(db: Session, reader_id: UUID, book_id: int, value: int) -> Rating:
    if not 1 <= value <= 5:
        raise ValueError("Rating must be between 1 and 5")
    if db.scalar(select(Book.id).where(Book.id == book_id)) is None:
        raise UnknownBookError("Book not found")

    statement = (
        insert(Rating)
        .values(reader_id=reader_id, book_id=book_id, value=value)
        .on_conflict_do_update(
            constraint="uq_ratings_reader_book",
            set_={"value": value, "updated_at": func.now()},
        )
        .returning(Rating)
    )
    rating = db.execute(statement).scalar_one()
    db.commit()
    return rating
