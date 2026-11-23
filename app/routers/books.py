from fastapi import APIRouter, status

from app.data import BOOKS
from app.errors import AppError
from app.schemas import BookCreate, BookRead, BookUpdate

router = APIRouter(prefix="/books", tags=["도서"])

def find_book(book_id: int) -> dict:
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    raise AppError(404, "BOOK_NOT_FOUND", f"{book_id}번 도서를 찾을 수 없습니다.")

def check_isbn_unique(isbn: str | None, exclude_id: int | None = None) -> None:
    """같은 ISBN이 이미 있으면 409 오류를 냅니다. 수정할 때는 자기 자신을 빼고 비교합니다."""
    if isbn is None:
        return
    for book in BOOKS:
        if book["isbn"] == isbn and book["id"] != exclude_id:
            raise AppError(409, "DUPLICATE_ISBN", "이미 등록된 ISBN입니다.")

@router.get("", response_model=list[BookRead], summary="도서 목록 조회")
def list_books(author: str | None = None):
    """저자 이름(author)을 주면 그 저자의 도서만 돌려줍니다."""
    if author is None:
        return BOOKS
    return [book for book in BOOKS if book["author"] == author]

@router.get("/{book_id}", response_model=BookRead, summary="도서 상세 조회",
            responses={404: {"description": "도서를 찾을 수 없음"}})
def get_book(book_id: int):
    return find_book(book_id)

@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED, summary="도서 등록",
             responses={409: {"description": "이미 등록된 ISBN"}})
def create_book(book_in: BookCreate):
    check_isbn_unique(book_in.isbn)
    new_id = max(book["id"] for book in BOOKS) + 1 if BOOKS else 1
    book = {"id": new_id, **book_in.model_dump(), "cost": 0}
    BOOKS.append(book)
    return book

@router.put("/{book_id}", response_model=BookRead, summary="도서 전체 수정")
def replace_book(book_id: int, book_in: BookCreate):
    book = find_book(book_id)
    check_isbn_unique(book_in.isbn, exclude_id=book_id)
    book.update(book_in.model_dump())
    return book

@router.patch("/{book_id}", response_model=BookRead, summary="도서 일부 수정")
def update_book(book_id: int, book_in: BookUpdate):
    book = find_book(book_id)
    changes = book_in.model_dump(exclude_unset=True, exclude_none=True)
    check_isbn_unique(changes.get("isbn"), exclude_id=book_id)
    book.update(changes)
    return book

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="도서 삭제")
def delete_book(book_id: int):
    book = find_book(book_id)
    BOOKS.remove(book)
