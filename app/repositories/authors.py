"""저자 저장소"""
from sqlalchemy.orm import Session

from app.models import Author

def get(db: Session, author_id: int) -> Author | None:
    return db.get(Author, author_id)
