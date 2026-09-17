from math import ceil
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.dependencies import get_current_reader
from app.models import Reader
from app.repositories import books as book_repository
from app.repositories import ratings as rating_repository
from app.security import csrf_token, require_csrf

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _context(request: Request, **values: object) -> dict[str, object]:
    return {"request": request, "csrf_token": csrf_token(request), **values}


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    saved: bool = Query(default=False),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    reader: Reader = Depends(get_current_reader),
) -> HTMLResponse:
    recommendations, personalized = book_repository.get_content_recommendations(
        db, reader.id, settings.recommendation_limit
    )
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context=_context(
            request,
            total_read=book_repository.count_read_books(db, reader.id),
            recommendations=recommendations,
            personalized=personalized,
            saved=saved,
        ),
    )


@router.get("/read", response_class=HTMLResponse)
def read_books(
    request: Request,
    page: int = Query(default=1, ge=1, le=10_000),
    db: Session = Depends(get_db),
    reader: Reader = Depends(get_current_reader),
) -> HTMLResponse:
    page_size = 18
    books, total = book_repository.get_read_books(db, reader.id, page, page_size)
    pages = max(1, ceil(total / page_size))
    if page > pages and total:
        return RedirectResponse(url=f"/read?page={pages}", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="read_books.html",
        context=_context(request, books=books, total=total, page=page, pages=pages),
    )


@router.get("/books/{book_id}", response_class=HTMLResponse)
def book_detail(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
    reader: Reader = Depends(get_current_reader),
) -> HTMLResponse:
    book = book_repository.get_book(db, book_id)
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return templates.TemplateResponse(
        request=request,
        name="book_detail.html",
        context=_context(
            request,
            book=book,
            rating=book_repository.get_book_rating(db, book_id, reader.id),
        ),
    )


@router.post("/ratings")
def save_rating_form(
    request: Request,
    book_id: int = Form(gt=0),
    rating: int = Form(ge=1, le=5),
    csrf: str = Form(),
    return_to: str = Form(default="/"),
    db: Session = Depends(get_db),
    reader: Reader = Depends(get_current_reader),
) -> RedirectResponse:
    require_csrf(request, csrf)
    try:
        rating_repository.save_rating(db, reader.id, book_id, rating)
    except rating_repository.UnknownBookError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    safe_return = return_to if return_to.startswith("/") and not return_to.startswith("//") else "/"
    separator = "&" if "?" in safe_return else "?"
    return RedirectResponse(
        url=f"{safe_return}{separator}saved=true&book={quote(str(book_id))}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
