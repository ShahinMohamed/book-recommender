from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

EMBEDDING_DIMENSIONS = 384


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dataset_index: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(750), nullable=False)
    authors: Mapped[str | None] = mapped_column(String(1000))
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(1000))
    publisher: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    publish_month: Mapped[str | None] = mapped_column(String(20))
    publish_year: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    ratings: Mapped[list["Rating"]] = relationship(back_populates="book", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_books_title", "title"),
        Index("ix_books_category", "category"),
    )


class Reader(Base):
    __tablename__ = "readers"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ratings: Mapped[list["Rating"]] = relationship(back_populates="reader", cascade="all, delete-orphan")


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reader_id: Mapped[UUID] = mapped_column(ForeignKey("readers.id", ondelete="CASCADE"), nullable=False)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    reader: Mapped[Reader] = relationship(back_populates="ratings")
    book: Mapped[Book] = relationship(back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("reader_id", "book_id", name="uq_ratings_reader_book"),
        CheckConstraint("value BETWEEN 1 AND 5", name="ck_ratings_value"),
        Index("ix_ratings_reader_id", "reader_id"),
        Index("ix_ratings_book_id", "book_id"),
    )
