import os

# app을 불러오기 전에 테스트용 비밀 키를 넣습니다. 환경 변수는 .env보다 먼저 쓰입니다.
# .env가 없는 CI 서버에서도 테스트가 돌아가게 하려는 것입니다.
os.environ["SECRET_KEY"] = "test-secret-key-only-for-pytest-0123456789"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Author

# 메모리 안에만 만드는 SQLite. 파일이 생기지 않고, 연결을 하나만 써서 테이블을 함께 봅니다.
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)

@pytest.fixture
def db_session():
    """테스트마다 빈 테이블을 만들고, 테스트가 끝나면 모두 지웁니다."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """테스트용 데이터베이스를 쓰는 TestClient"""

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db  # get_db 대신 이 함수를 쓰게 합니다.
    yield TestClient(app)
    app.dependency_overrides.clear()  # 다른 테스트에 영향을 주지 않도록 원래대로 돌립니다.

@pytest.fixture
def author_id(db_session):
    """테스트용 저자. API를 거치지 않고 데이터베이스에 바로 넣습니다."""
    author = Author(name="테스트 저자")
    db_session.add(author)
    db_session.commit()
    return author.id

@pytest.fixture
def auth_headers(client):
    """가입하고 로그인한 사용자의 Authorization 헤더"""
    client.post("/auth/signup", json={"email": "tester@example.com", "password": "test-pass-123"})
    response = client.post("/auth/token", data={"username": "tester@example.com", "password": "test-pass-123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
