"""보안 테스트 준비: 테스트마다 빈 임시 폴더에서 게시판 앱을 새로 불러옵니다."""
import importlib
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

LAB_DIR = Path(__file__).resolve().parent.parent  # app.py가 있는 폴더
sys.path.insert(0, str(LAB_DIR))

@pytest.fixture
def board(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # board.db와 uploads 폴더가 임시 폴더에 생깁니다.
    monkeypatch.setenv("SECRET_KEY", "test-only-secret-key-0123456789abcdef")
    sys.modules.pop("app", None)
    return importlib.import_module("app")

@pytest.fixture
def client(board):
    return TestClient(board.app, raise_server_exceptions=False)

@pytest.fixture
def login(client):
    """회원가입과 로그인을 하고, 요청 헤더를 돌려주는 함수를 줍니다."""
    def _login(username: str, password: str = "club-pass-1234") -> dict:
        client.post("/signup", json={"username": username, "password": password})
        token = client.post("/login", json={"username": username, "password": password}).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return _login

@pytest.fixture
def notice(client, login):
    """alice가 쓴 공지 하나를 만들고 번호를 돌려줍니다."""
    headers = login("alice")
    return client.post("/notices", json={"title": "정기 모임 안내", "body": "금요일 7시"}, headers=headers).json()["id"]

@pytest.fixture
def admin_headers(client, login):
    """관리자 계정을 만들고 로그인한 헤더를 돌려줍니다."""
    login("admin1")
    with sqlite3.connect("board.db") as conn:
        conn.execute("UPDATE users SET role = 'admin' WHERE username = 'admin1'")
    return login("admin1")
