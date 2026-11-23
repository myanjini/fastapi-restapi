"""대여 서비스"""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Loan, User
from app.repositories import loans as loan_repo
from app.services.books import change_stock, find_book

logger = logging.getLogger(__name__)

MAX_ACTIVE_LOANS = 3  # 한 사람이 동시에 빌릴 수 있는 권수

def borrow(db: Session, user: User, book_id: int) -> Loan:
    book = find_book(db, book_id)
    if loan_repo.find_active(db, user.id, book.id) is not None:
        raise AppError(409, "ALREADY_LOANED", "이미 빌린 도서입니다. 반납한 뒤 다시 빌릴 수 있습니다.")
    if loan_repo.count_active(db, user.id) >= MAX_ACTIVE_LOANS:
        raise AppError(409, "LOAN_LIMIT_EXCEEDED", f"한 번에 {MAX_ACTIVE_LOANS}권까지 빌릴 수 있습니다.")
    if book.stock < 1:
        raise AppError(409, "OUT_OF_STOCK", "남은 재고가 없습니다.")

    # 재고 감소, 재고 기록, 대여 기록을 하나의 트랜잭션으로 묶습니다.
    change_stock(db, book, -1, "대여")
    loan = loan_repo.add(db, Loan(user_id=user.id, book_id=book.id))
    db.commit()
    db.refresh(loan)
    logger.info("도서 대여", extra={"user_id": user.id, "book_id": book.id, "loan_id": loan.id})
    return loan

def return_book(db: Session, user: User, loan_id: int) -> Loan:
    loan = loan_repo.get(db, loan_id)
    if loan is None:
        raise AppError(404, "LOAN_NOT_FOUND", f"{loan_id}번 대여 기록을 찾을 수 없습니다.")
    if loan.user_id != user.id and user.role != "admin":
        raise AppError(403, "FORBIDDEN", "본인이 빌린 도서만 반납할 수 있습니다.")
    if loan.returned_at is not None:
        raise AppError(409, "ALREADY_RETURNED", "이미 반납한 도서입니다.")

    loan.returned_at = datetime.now(timezone.utc)
    change_stock(db, loan.book, 1, "반납")
    db.commit()
    db.refresh(loan)
    return loan

def my_loans(db: Session, user: User) -> list[Loan]:
    return loan_repo.list_by_user(db, user.id)
