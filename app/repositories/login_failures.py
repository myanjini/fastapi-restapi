"""로그인 실패 기록 저장소"""
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import LoginFailure

def count_since(db: Session, since: datetime, *, email: str | None = None, ip: str | None = None) -> int:
    stmt = select(func.count()).select_from(LoginFailure).where(LoginFailure.created_at > since)
    if email is not None:
        stmt = stmt.where(LoginFailure.email == email)
    if ip is not None:
        stmt = stmt.where(LoginFailure.ip == ip)
    return db.scalar(stmt)

def add(db: Session, email: str, ip: str, at: datetime) -> None:
    db.add(LoginFailure(email=email, ip=ip, created_at=at))

def clear(db: Session, email: str) -> None:
    db.execute(delete(LoginFailure).where(LoginFailure.email == email))
