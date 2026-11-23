from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import PageDep, SessionDep
from app.errors import AppError
from app.models import Book
from app.schemas import BookCreate, BookRead

router = APIRouter(prefix="/books", tags=["도서"])

def find_book(db: Session, book_id: int) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise AppError(404, "BOOK_NOT_FOUND", f"{book_id}번 도서를 찾을 수 없습니다.")
    return book

def check_isbn_unique(db: Session, isbn: str | None, exclude_id: int | None = None) -> None:
    if isbn is None:
        return
    found = db.scalar(select(Book).where(Book.isbn == isbn))
    if found is not None and found.id != exclude_id:
        raise AppError(409, "DUPLICATE_ISBN", "이미 등록된 ISBN입니다.")

@router.get("", response_model=list[BookRead], summary="도서 목록 조회")
def list_books(db: SessionDep, page: PageDep, author: str | None = None):
    stmt = select(Book)
    if author is not None:
        stmt = stmt.where(Book.author == author)
    stmt = stmt.order_by(Book.id).offset(page.skip).limit(page.limit)
    return db.scalars(stmt).all()

@router.get("/{book_id}", response_model=BookRead, summary="도서 상세 조회",
            responses={404: {"description": "도서를 찾을 수 없음"}})
def get_book(db: SessionDep, book_id: int):
    return find_book(db, book_id)

@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED, summary="도서 등록",
             responses={409: {"description": "이미 등록된 ISBN"}})
def create_book(db: SessionDep, book_in: BookCreate):
    check_isbn_unique(db, book_in.isbn)
    book = Book(**book_in.model_dump())
    db.add(book)      # 저장할 목록에 올립니다.
    db.commit()       # 데이터베이스에 실제로 저장합니다.
    db.refresh(book)  # 데이터베이스가 정한 id를 다시 읽어 옵니다.
    return book
