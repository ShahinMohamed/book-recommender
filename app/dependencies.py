from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Reader


def get_current_reader(request: Request, db: Session = Depends(get_db)) -> Reader:
    raw_id = request.session.get("reader_id")
    reader = None
    if raw_id:
        try:
            reader = db.get(Reader, UUID(str(raw_id)))
        except ValueError:
            reader = None

    if reader is None:
        reader = Reader()
        db.add(reader)
        db.commit()
        db.refresh(reader)
        request.session["reader_id"] = str(reader.id)
    else:
        db.execute(Reader.__table__.update().where(Reader.id == reader.id).values(last_seen_at=func.now()))
        db.commit()
    return reader
