from typing import Literal

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import PageDep, SessionDep
from app.errors import AppError
from app.models import Book
from app.schemas import BookCreate, BookPage, BookRead, BookUpdate

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

# 정렬 기준으로 받을 수 있는 값과 실제 정렬 방법을 짝지어 둡니다.
SORT_OPTIONS = {
    "id": Book.id,
    "price": Book.price,
    "-price": Book.price.desc(),
}

@router.get("", response_model=BookPage, summary="도서 목록 조회")
def list_books(
    db: SessionDep,
    page: PageDep,
    q: str | None = Query(default=None, max_length=50, description="제목에 들어간 글자로 검색"),
    author: str | None = Query(default=None, description="저자 이름"),
    sort: Literal["id", "price", "-price"] = Query(default="id", description="정렬 기준"),
):
    conditions = []
    if q is not None:
        conditions.append(Book.title.contains(q))
    if author is not None:
        conditions.append(Book.author == author)

    total = db.scalar(select(func.count()).select_from(Book).where(*conditions))
    stmt = (
        select(Book)
        .where(*conditions)
        .order_by(SORT_OPTIONS[sort], Book.id)
        .offset(page.skip)
        .limit(page.limit)
    )
    items = db.scalars(stmt).all()
    return {"items": items, "total": total, "skip": page.skip, "limit": page.limit}

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

@router.patch("/{book_id}", response_model=BookRead, summary="도서 일부 수정",
              responses={404: {"description": "도서를 찾을 수 없음"}, 409: {"description": "이미 등록된 ISBN"}})
def update_book(db: SessionDep, book_id: int, book_in: BookUpdate):
    book = find_book(db, book_id)
    changes = book_in.model_dump(exclude_unset=True, exclude_none=True)
    check_isbn_unique(db, changes.get("isbn"), exclude_id=book_id)
    for field, value in changes.items():
        setattr(book, field, value)  # book.price = 19000 과 같은 뜻입니다.
    db.commit()
    db.refresh(book)
    return book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="도서 삭제",
               responses={404: {"description": "도서를 찾을 수 없음"}})
def delete_book(db: SessionDep, book_id: int):
    book = find_book(db, book_id)
    db.delete(book)
    db.commit()
