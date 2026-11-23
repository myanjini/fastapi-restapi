"""사용자 저장소"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

def list_users(db: Session, skip: int, limit: int) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id).offset(skip).limit(limit)).all())
