"""관리자 지정 도구. 사용법: python -m app.make_admin user2@example.com"""
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User

email = sys.argv[1].lower()
with SessionLocal() as db:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        print(f"{email} 사용자가 없습니다.")
        sys.exit(1)
    user.role = "admin"
    db.commit()
    print(f"{email} 사용자를 관리자로 바꿨습니다.")
