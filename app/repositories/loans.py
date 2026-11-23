"""대여 저장소"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Loan

def get(db: Session, loan_id: int) -> Loan | None:
    return db.get(Loan, loan_id)

def find_active(db: Session, user_id: int, book_id: int) -> Loan | None:
    """이 사용자가 이 도서를 빌린 뒤 아직 반납하지 않은 기록을 찾습니다."""
    return db.scalar(select(Loan).where(
        Loan.user_id == user_id, Loan.book_id == book_id, Loan.returned_at.is_(None)))

def count_active(db: Session, user_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Loan).where(
        Loan.user_id == user_id, Loan.returned_at.is_(None)))

def exists_for_book(db: Session, book_id: int) -> bool:
    return db.scalar(select(Loan.id).where(Loan.book_id == book_id).limit(1)) is not None

def list_by_user(db: Session, user_id: int) -> list[Loan]:
    stmt = (select(Loan).options(selectinload(Loan.book))
            .where(Loan.user_id == user_id).order_by(Loan.id.desc()))
    return list(db.scalars(stmt).all())

def add(db: Session, loan: Loan) -> Loan:
    db.add(loan)
    db.flush()
    return loan
