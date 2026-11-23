from typing import Literal

from fastapi import APIRouter, Query, UploadFile, status

from app.dependencies import CurrentUserDep, PageDep, SessionDep
from app.schemas import BookCreate, BookPage, BookRead, BookUpdate, StockChange
from app.services import books as book_service

router = APIRouter(prefix="/books", tags=["도서"])

FORBIDDEN_OR_NOT_FOUND = {401: {"description": "로그인 필요"}, 403: {"description": "권한 없음"},
                          404: {"description": "도서를 찾을 수 없음"}}

@router.get("", response_model=BookPage, summary="도서 목록 조회")
def list_books(
    db: SessionDep,
    page: PageDep,
    q: str | None = Query(default=None, max_length=50, description="제목에 들어간 글자로 검색"),
    author_id: int | None = Query(default=None, description="저자 번호"),
    sort: Literal["id", "price", "-price"] = Query(default="id", description="정렬 기준"),
):
    return book_service.list_books(db, q, author_id, sort, page.skip, page.limit)

@router.get("/{book_id}", response_model=BookRead, summary="도서 상세 조회",
            responses={404: {"description": "도서를 찾을 수 없음"}})
def get_book(db: SessionDep, book_id: int):
    return book_service.find_book(db, book_id)

@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED, summary="도서 등록",
             responses={401: {"description": "로그인 필요"}, 409: {"description": "이미 등록된 ISBN"}})
def create_book(db: SessionDep, user: CurrentUserDep, book_in: BookCreate):
    return book_service.create_book(db, user, book_in)

@router.patch("/{book_id}", response_model=BookRead, summary="도서 일부 수정",
              responses={**FORBIDDEN_OR_NOT_FOUND, 409: {"description": "이미 등록된 ISBN"}})
def update_book(db: SessionDep, user: CurrentUserDep, book_id: int, book_in: BookUpdate):
    return book_service.update_book(db, user, book_id, book_in)

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="도서 삭제",
               responses=FORBIDDEN_OR_NOT_FOUND)
def delete_book(db: SessionDep, user: CurrentUserDep, book_id: int):
    book_service.delete_book(db, user, book_id)

@router.post("/{book_id}/stock", response_model=BookRead, summary="재고 변경",
             responses={**FORBIDDEN_OR_NOT_FOUND, 409: {"description": "재고 부족"}})
def adjust_stock(db: SessionDep, user: CurrentUserDep, book_id: int, data: StockChange):
    return book_service.adjust_stock(db, user, book_id, data)

@router.post("/{book_id}/cover", response_model=BookRead, summary="표지 이미지 업로드",
             responses={**FORBIDDEN_OR_NOT_FOUND, 413: {"description": "2MB 초과"},
                        415: {"description": "jpg, jpeg, png가 아님"}})
def upload_book_cover(db: SessionDep, user: CurrentUserDep, book_id: int, file: UploadFile):
    return book_service.upload_cover(db, user, book_id, file)
