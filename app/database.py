from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# SQLite는 기본적으로 한 스레드에서만 연결을 쓰게 되어 있어 이 옵션을 끕니다.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase):
    """모든 모델 클래스가 상속하는 기본 클래스입니다."""

def get_db():
    """요청 하나에 세션 하나를 열어 주고, 요청이 끝나면 닫습니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
