from pydantic import BaseModel, ConfigDict, Field


class BookSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    authors: str | None
    category: str | None


class RatingCreate(BaseModel):
    book_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)


class RatingResult(BaseModel):
    book_id: int
    rating: int
    total_read: int
