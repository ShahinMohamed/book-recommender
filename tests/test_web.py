import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.models import Rating, Reader

pytestmark = pytest.mark.integration


def _csrf(response) -> str:
    match = re.search(r'<meta name="csrf-token" content="([^"]+)">', response.text)
    assert match
    return match.group(1)


def test_rating_flow_and_all_dataset_fields():
    with SessionLocal() as db:
        db.execute(delete(Rating))
        db.execute(delete(Reader))
        db.commit()

    with TestClient(app) as client:
        home = client.get("/")
        assert home.status_code == 200
        assert "books read" in home.text
        token = _csrf(home)

        search = client.get("/api/books/search", params={"q": "The Hobbit"})
        assert search.status_code == 200
        matches = search.json()
        assert matches
        book_id = matches[0]["id"]

        saved = client.post(
            "/api/ratings",
            headers={"X-CSRF-Token": token},
            json={"book_id": book_id, "rating": 5},
        )
        assert saved.status_code == 201
        assert saved.json()["total_read"] == 1

        read = client.get("/read")
        assert read.status_code == 200
        assert "5 / 5" in read.text
        assert 'href="/">← Back to homepage</a>' in read.text

        detail = client.get(f"/books/{book_id}")
        assert detail.status_code == 200
        for column_label in [
            "Title",
            "Author",
            "Genre / category",
            "Publisher",
            "Starting price",
            "Publication date",
        ]:
            assert column_label in detail.text


def test_csrf_is_required_for_rating_mutations():
    with TestClient(app) as client:
        response = client.post("/api/ratings", json={"book_id": 1, "rating": 5})
        assert response.status_code == 403
