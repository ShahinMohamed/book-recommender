"""Create catalog, anonymous readers, ratings, and vector indexes."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector


revision: str = "20260912_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "books",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("dataset_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=750), nullable=False),
        sa.Column("authors", sa.String(length=1000), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=1000), nullable=True),
        sa.Column("publisher", sa.String(length=500), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("publish_month", sa.String(length=20), nullable=True),
        sa.Column("publish_year", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(dim=384), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("dataset_index", name="uq_books_dataset_index"),
    )
    op.create_index("ix_books_title", "books", ["title"])
    op.create_index("ix_books_category", "books", ["category"])
    op.create_index(
        "ix_books_title_trgm", "books", ["title"], postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}
    )
    op.create_index(
        "ix_books_embedding_hnsw",
        "books",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"m": 16, "ef_construction": 64},
    )
    op.create_table(
        "readers",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_table(
        "ratings",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("reader_id", sa.Uuid(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("value BETWEEN 1 AND 5", name="ck_ratings_value"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reader_id"], ["readers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("reader_id", "book_id", name="uq_ratings_reader_book"),
    )
    op.create_index("ix_ratings_reader_id", "ratings", ["reader_id"])
    op.create_index("ix_ratings_book_id", "ratings", ["book_id"])


def downgrade() -> None:
    op.drop_table("ratings")
    op.drop_table("readers")
    op.drop_table("books")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS vector")
