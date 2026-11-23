"""보안약점을 고친 뒤 다시 생기지 않는지 확인하는 테스트"""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from pydantic import ValidationError

from app.config import Settings
from app.privacy import mask_text
from app.routers import files
from app.services import covers
from tests.conftest import TEST_KEY
from tests.helpers import create_book

SQLI = "zz%' UNION SELECT email, hashed_password, 0 FROM users --"

def test_report_sql_injection_does_not_leak_users(client, auth_headers, author_id):
    create_book(client, auth_headers, author_id, title="파이썬 첫걸음", stock=3)
    response = client.get("/reports/stock", params={"keyword": SQLI}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []  # 그런 제목의 도서가 없을 뿐, 사용자 정보는 나오지 않습니다.

def test_report_rejects_unknown_order_by(client, auth_headers):
    response = client.get("/reports/stock", params={"order_by": "stock; DROP TABLE books"}, headers=auth_headers)
    assert response.status_code == 422

@pytest.mark.parametrize("name", ["../.env", "../app/config.py", "/etc/passwd", "..\\.env"])
def test_download_blocks_path_traversal(client, name):
    response = client.get("/files/download", params={"name": name})
    assert response.status_code in (400, 422)

def test_download_file(client, tmp_path, monkeypatch):
    (tmp_path / "guide.txt").write_text("이용 안내", encoding="utf-8")
    monkeypatch.setattr(files, "FILES_DIR", tmp_path.resolve())
    response = client.get("/files/download", params={"name": "guide.txt"})
    assert response.status_code == 200
    assert response.text == "이용 안내"
    assert "attachment" in response.headers["content-disposition"]

def test_responses_have_nosniff_header(client):
    assert client.get("/health").headers["X-Content-Type-Options"] == "nosniff"

def test_upload_html_disguised_as_png_returns_415(client, auth_headers, author_id, tmp_path, monkeypatch):
    monkeypatch.setattr(covers, "COVER_DIR", tmp_path)
    book = create_book(client, auth_headers, author_id)
    fake = b"<html><script>alert(document.cookie)</script></html>"
    response = client.post(f"/books/{book['id']}/cover", headers=auth_headers,
                           files={"file": ("cover.png", fake, "image/png")})
    assert response.status_code == 415
    assert response.json()["code"] == "INVALID_IMAGE_CONTENT"
    assert list(tmp_path.iterdir()) == []  # 아무 파일도 저장되지 않았습니다.

def test_clean_filename():
    assert covers.clean_filename("../../etc/passwd") == "passwd"
    assert covers.clean_filename("a\nb.png") == "ab.png"
    assert covers.clean_filename("") == "unnamed"

def test_cannot_read_others_loan(client, make_user, author_id):
    user1 = make_user("user1@example.com")
    user3 = make_user("user3@example.com")
    book = create_book(client, user1, author_id, stock=1)
    loan = client.post("/loans", json={"book_id": book["id"]}, headers=user1).json()

    assert client.get(f"/loans/{loan['id']}", headers=user1).status_code == 200
    response = client.get(f"/loans/{loan['id']}", headers=user3)
    assert response.status_code == 404  # 남의 기록은 있다는 사실도 알려 주지 않습니다.

@pytest.mark.parametrize("path", ["/admin/users", "/admin/loans"])
def test_admin_api_forbidden_for_user(client, auth_headers, path):
    assert client.get(path, headers=auth_headers).status_code == 403

def test_admin_api_for_admin(client, make_user):
    admin = make_user("admin@example.com", role="admin")
    response = client.get("/admin/users", headers=admin)
    assert response.status_code == 200
    assert "hashed_password" not in response.json()[0]

def test_signup_with_role_field_returns_422(client):
    response = client.post("/auth/signup", json={"email": "x@example.com", "password": "test-pass-123", "role": "admin"})
    assert response.status_code == 422

def test_update_book_with_unknown_field_returns_422(client, auth_headers, author_id):
    book = create_book(client, auth_headers, author_id)
    response = client.patch(f"/books/{book['id']}", json={"owner_id": 999}, headers=auth_headers)
    assert response.status_code == 422

def test_weak_secret_key_is_rejected():
    for weak in ["change-me", "short-key"]:
        with pytest.raises(ValidationError):
            Settings(secret_key=weak, _env_file=None)

def test_admin_user_list_masks_email(client, make_user):
    admin = make_user("admin@example.com", role="admin")
    users = client.get("/admin/users", headers=admin).json()
    assert users[0]["email"] == "ad***@example.com"
    detail = client.get(f"/admin/users/{users[0]['id']}", headers=admin).json()
    assert detail["email"] == "admin@example.com"  # 상세 조회에서만 전체를 보여 줍니다.

def login(client, email, password):
    return client.post("/auth/token", data={"username": email, "password": password})

def test_login_is_locked_after_five_failures(client, make_user):
    make_user("user1@example.com")
    for _ in range(5):
        assert login(client, "user1@example.com", "wrong-pass-0").status_code == 401
    response = login(client, "user1@example.com", "test-pass-123")  # 맞는 비밀번호여도 잠깁니다.
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "900"

def test_successful_login_resets_failures(client, make_user):
    make_user("user1@example.com")
    for _ in range(4):
        login(client, "user1@example.com", "wrong-pass-0")
    assert login(client, "user1@example.com", "test-pass-123").status_code == 200
    for _ in range(4):
        login(client, "user1@example.com", "wrong-pass-0")
    assert login(client, "user1@example.com", "test-pass-123").status_code == 200

@pytest.mark.parametrize("password", ["short-pw1", "password1234", "aaaaaaaaaaaa", "mybook-mybook-1"])
def test_weak_password_is_rejected(client, password):
    response = client.post("/auth/signup", json={"email": "mybook@example.com", "password": password})
    assert response.status_code == 422

def make_token(payload: dict, key: str = TEST_KEY, algorithm: str = "HS256") -> str:
    return jwt.encode(payload, key, algorithm=algorithm)

@pytest.mark.parametrize("token", [
    make_token({"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}),    # 만료
    make_token({"sub": "1"}),                                                               # exp 없음
    make_token({"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, "other-key-" * 4),  # 다른 키
    make_token({"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, None, "none"),     # 서명 없음
])
def test_invalid_tokens_are_rejected(client, make_user, token):
    make_user("user1@example.com")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

def test_unexpected_error_hides_details(client, auth_headers, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("database password is pg-secret-0123")
    monkeypatch.setattr("app.services.books.list_books", broken)

    response = client.get("/books")
    body = response.json()
    assert response.status_code == 500
    assert body["code"] == "INTERNAL_ERROR"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert "pg-secret" not in response.text and "RuntimeError" not in response.text

def test_validation_error_does_not_echo_input(client):
    response = client.post("/auth/signup", json={"email": "new@example.com", "password": "my-pw-123"})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "my-pw-123" not in response.text

def test_mask_text():
    line = "user1@example.com eyJhbGciOi.eyJzdWIiOi.abc $argon2id$v=19$m=65536$salt$hash"
    assert mask_text(line) == "us***@example.com [TOKEN] [PASSWORD_HASH]"
