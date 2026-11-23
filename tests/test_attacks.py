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
