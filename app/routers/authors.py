from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import PageDep, SessionDep, require_admin
from app.errors import AppError
from app.models import Author
from app.schemas import AuthorCreate, AuthorRead, BookRead

router = APIRouter(prefix="/authors", tags=["저자"])

def find_author(db: Session, author_id: int) -> Author:
    author = db.get(Author, author_id)
    if author is None:
        raise AppError(404, "AUTHOR_NOT_FOUND", f"{author_id}번 저자를 찾을 수 없습니다.")
    return author

@router.post("", response_model=AuthorRead, status_code=status.HTTP_201_CREATED, summary="저자 등록",
             dependencies=[Depends(require_admin)],  # 관리자만 호출할 수 있습니다.
             responses={409: {"description": "이미 등록된 저자 이름"}})
def create_author(db: SessionDep, author_in: AuthorCreate):
    if db.scalar(select(Author).where(Author.name == author_in.name)) is not None:
        raise AppError(409, "DUPLICATE_AUTHOR", "이미 등록된 저자입니다.")
    author = Author(name=author_in.name)
    db.add(author)
    db.commit()
    db.refresh(author)
    return author

@router.get("", response_model=list[AuthorRead], summary="저자 목록 조회")
def list_authors(db: SessionDep, page: PageDep):
    stmt = select(Author).order_by(Author.id).offset(page.skip).limit(page.limit)
    return db.scalars(stmt).all()

@router.get("/{author_id}", response_model=AuthorRead, summary="저자 상세 조회",
            responses={404: {"description": "저자를 찾을 수 없음"}})
def get_author(db: SessionDep, author_id: int):
    return find_author(db, author_id)

@router.get("/{author_id}/books", response_model=list[BookRead], summary="저자별 도서 목록")
def list_author_books(db: SessionDep, author_id: int):
    author = find_author(db, author_id)
    return author.books

@router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT, summary="저자 삭제",
               dependencies=[Depends(require_admin)],
               responses={404: {"description": "저자를 찾을 수 없음"}, 409: {"description": "도서가 남아 있는 저자"}})
def delete_author(db: SessionDep, author_id: int):
    author = find_author(db, author_id)
    if author.books:
        raise AppError(409, "AUTHOR_HAS_BOOKS", "이 저자의 도서가 남아 있어 삭제할 수 없습니다.")
    db.delete(author)
    db.commit()
