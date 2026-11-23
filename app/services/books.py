"""도서 서비스: 규칙 검사와 트랜잭션(commit)을 맡습니다. HTTP 요청과 응답은 모릅니다."""
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Book, User
from app.repositories import authors as author_repo
from app.repositories import books as book_repo
from app.schemas import BookCreate, BookUpdate, StockChange

def find_book(db: Session, book_id: int) -> Book:
    book = book_repo.get(db, book_id)
    if book is None:
        raise AppError(404, "BOOK_NOT_FOUND", f"{book_id}번 도서를 찾을 수 없습니다.")
    return book

def check_isbn_unique(db: Session, isbn: str | None, exclude_id: int | None = None) -> None:
    if isbn is None:
        return
    found = book_repo.get_by_isbn(db, isbn)
    if found is not None and found.id != exclude_id:
        raise AppError(409, "DUPLICATE_ISBN", "이미 등록된 ISBN입니다.")

def check_author_exists(db: Session, author_id: int | None) -> None:
    if author_id is None:
        return
    if author_repo.get(db, author_id) is None:
        raise AppError(422, "INVALID_AUTHOR", f"{author_id}번 저자가 없습니다.")

def check_can_modify(book: Book, user: User) -> None:
    """도서를 등록한 사람이나 관리자만 수정, 삭제할 수 있습니다."""
    if user.role == "admin" or book.owner_id == user.id:
        return
    raise AppError(403, "FORBIDDEN", "이 도서를 수정하거나 삭제할 권한이 없습니다.")

def change_stock(db: Session, book: Book, change: int, reason: str) -> None:
    """재고를 바꾸고 기록을 남깁니다. 확정(commit)은 이 함수를 부른 쪽에서 합니다."""
    if book.stock + change < 0:
        raise AppError(409, "INSUFFICIENT_STOCK", f"재고가 부족합니다. 현재 재고는 {book.stock}권입니다.")
    book.stock += change
    book_repo.add_stock_log(db, book, change, reason)

def create_book(db: Session, user: User, book_in: BookCreate) -> Book:
    check_isbn_unique(db, book_in.isbn)
    check_author_exists(db, book_in.author_id)
    book = book_repo.add(db, Book(**book_in.model_dump(exclude={"stock"}), owner_id=user.id))
    if book_in.stock > 0:
        change_stock(db, book, book_in.stock, "입고")
    db.commit()  # 도서 등록과 재고 기록을 한 번에 확정합니다.
    db.refresh(book)
    return book

def list_books(db: Session, q: str | None, author_id: int | None, sort: str,
               skip: int, limit: int) -> dict:
    items, total = book_repo.search(db, q, author_id, sort, skip, limit)
    return {"items": items, "total": total, "skip": skip, "limit": limit}

def update_book(db: Session, user: User, book_id: int, book_in: BookUpdate) -> Book:
    book = find_book(db, book_id)
    check_can_modify(book, user)
    changes = book_in.model_dump(exclude_unset=True, exclude_none=True)
    check_isbn_unique(db, changes.get("isbn"), exclude_id=book_id)
    check_author_exists(db, changes.get("author_id"))
    for field, value in changes.items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return book

def delete_book(db: Session, user: User, book_id: int) -> None:
    book = find_book(db, book_id)
    check_can_modify(book, user)
    book_repo.delete(db, book)  # 재고 기록도 함께 지워집니다(cascade).
    db.commit()

def adjust_stock(db: Session, user: User, book_id: int, data: StockChange) -> Book:
    book = find_book(db, book_id)
    check_can_modify(book, user)
    change_stock(db, book, data.change, data.reason)
    db.commit()
    db.refresh(book)
    return book
