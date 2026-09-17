from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.dependencies import get_current_reader
from app.models import Reader
from app.repositories import books as book_repository
from app.repositories import ratings as rating_repository
from app.schemas import BookSearchResult, RatingCreate, RatingResult
from app.security import require_csrf

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/books/search", response_model=list[BookSearchResult])
def search_books(
    q: str = Query(min_length=2, max_length=120),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[BookSearchResult]:
    return [
        BookSearchResult.model_validate(book)
        for book in book_repository.search_books(db, q, settings.search_limit)
    ]


@router.post("/ratings", response_model=RatingResult, status_code=status.HTTP_201_CREATED)
def create_rating(
    payload: RatingCreate,
    request: Request,
    x_csrf_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
    reader: Reader = Depends(get_current_reader),
) -> RatingResult:
    require_csrf(request, x_csrf_token)
    try:
        result = rating_repository.save_rating(db, reader.id, payload.book_id, payload.rating)
    except rating_repository.UnknownBookError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RatingResult(
        book_id=result.book_id,
        rating=result.value,
        total_read=book_repository.count_read_books(db, reader.id),
    )
