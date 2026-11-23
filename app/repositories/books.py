"""도서 저장소: 데이터베이스에서 도서를 읽고 쓰는 코드만 둡니다. commit은 하지 않습니다."""
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.models import Book, StockLog

# 정렬 기준으로 받을 수 있는 값과 실제 정렬 방법을 짝지어 둡니다.
SORT_OPTIONS = {
    "id": Book.id,
    "price": Book.price,
    "-price": Book.price.desc(),
}

def get(db: Session, book_id: int) -> Book | None:
    return db.get(Book, book_id)

def get_by_isbn(db: Session, isbn: str) -> Book | None:
    return db.scalar(select(Book).where(Book.isbn == isbn))

def search(db: Session, q: str | None, author_id: int | None, sort: str,
           skip: int, limit: int) -> tuple[list[Book], int]:
    """조건에 맞는 도서 한 페이지와 전체 개수를 돌려줍니다."""
    conditions = []
    if q is not None:
        conditions.append(Book.title.contains(q))
    if author_id is not None:
        conditions.append(Book.author_id == author_id)

    total = db.scalar(select(func.count()).select_from(Book).where(*conditions))
    stmt = (
        select(Book)
        .options(selectinload(Book.author))
        .where(*conditions)
        .order_by(SORT_OPTIONS[sort], Book.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all()), total

def add(db: Session, book: Book) -> Book:
    db.add(book)
    db.flush()  # INSERT를 먼저 실행해 book.id를 받습니다. 확정(commit)은 아직 하지 않습니다.
    return book

def delete(db: Session, book: Book) -> None:
    db.delete(book)

def add_stock_log(db: Session, book: Book, change: int, reason: str) -> None:
    db.add(StockLog(book_id=book.id, change=change, reason=reason))

def add_to_stock(db: Session, book_id: int, change: int) -> bool:
    """재고를 데이터베이스 안에서 계산해 바꿉니다. 결과가 0보다 작아지면 바꾸지 않고 False를 돌려줍니다."""
    stmt = (
        update(Book)
        .where(Book.id == book_id, Book.stock + change >= 0)  # 조건을 만족할 때만 바꿉니다.
        .values(stock=Book.stock + change)                    # 지금 값에 더하는 계산을 데이터베이스가 합니다.
        .execution_options(synchronize_session=False)
    )
    return db.execute(stmt).rowcount == 1  # 바뀐 행이 1개면 성공, 0개면 조건을 만족하지 못한 것
