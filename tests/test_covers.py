from app.services import covers
from tests.helpers import create_book

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100  # PNG 파일처럼 시작하는 작은 데이터

def test_upload_cover(client, auth_headers, author_id, tmp_path, monkeypatch):
    # 실제 uploads 폴더 대신 pytest가 만들어 주는 임시 폴더를 쓰게 바꿉니다.
    monkeypatch.setattr(covers, "COVER_DIR", tmp_path)
    book = create_book(client, auth_headers, author_id)

    response = client.post(f"/books/{book['id']}/cover", headers=auth_headers,
                           files={"file": ("cover.png", PNG, "image/png")})

    assert response.status_code == 200
    saved = tmp_path / response.json()["cover_url"].removeprefix("/covers/")
    assert saved.read_bytes() == PNG

def test_upload_text_file_returns_415(client, auth_headers, author_id, tmp_path, monkeypatch):
    monkeypatch.setattr(covers, "COVER_DIR", tmp_path)
    book = create_book(client, auth_headers, author_id)
    response = client.post(f"/books/{book['id']}/cover", headers=auth_headers,
                           files={"file": ("note.txt", b"hello", "text/plain")})
    assert response.status_code == 415

def test_uploaded_cover_can_be_downloaded(client, auth_headers, author_id, tmp_path, monkeypatch):
    monkeypatch.setattr(covers, "COVER_DIR", tmp_path)
    book = create_book(client, auth_headers, author_id)
    url = client.post(f"/books/{book['id']}/cover", headers=auth_headers,
                      files={"file": ("cover.png", PNG, "image/png")}).json()["cover_url"]
    response = client.get(url)
    assert response.status_code == 200
    assert response.content == PNG
