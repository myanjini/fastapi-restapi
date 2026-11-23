"""보안약점을 고친 뒤 다시 생기지 않는지 확인하는 테스트"""
import pytest

from app.routers import files
from app.services import covers
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
