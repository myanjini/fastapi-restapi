from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def login(email: str = "user1@example.com", password: str = "practice-pass-1") -> dict:
    """로그인해 Authorization 헤더를 만듭니다. 개발용 데이터베이스의 user1을 씁니다."""
    response = client.post("/auth/token", data={"username": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

def create_book(headers: dict, **fields) -> dict:
    """테스트에 쓸 도서를 등록하고 응답 본문을 돌려줍니다."""
    data = {"title": "테스트 도서", "author_id": 1, "price": 10000} | fields
    response = client.post("/books", json=data, headers=headers)
    assert response.status_code == 201
    return response.json()

def test_health():
    # 실행
    response = client.get("/health")
    # 검증
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_books():
    response = client.get("/books")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert body["total"] >= 0

def test_get_missing_book_returns_404():
    response = client.get("/books/999999")
    assert response.status_code == 404
    assert response.json()["code"] == "BOOK_NOT_FOUND"

def test_create_book():
    # 준비
    headers = login()
    data = {"title": "테스트 도서", "author_id": 1, "price": 15000, "isbn": "9790000000017", "stock": 2}
    # 실행
    response = client.post("/books", json=data, headers=headers)
    # 검증
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "테스트 도서"
    assert body["stock"] == 2
    assert body["author"]["id"] == 1
    assert body["owner_id"] is not None

def test_get_book():
    book = create_book(login(), title="조회 테스트")
    response = client.get(f"/books/{book['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "조회 테스트"

def test_update_book():
    headers = login()
    book = create_book(headers)
    response = client.patch(f"/books/{book['id']}", json={"price": 20000}, headers=headers)
    assert response.status_code == 200
    assert response.json()["price"] == 20000
    # 다시 조회해도 바뀐 값이 나와야 합니다.
    assert client.get(f"/books/{book['id']}").json()["price"] == 20000

def test_delete_book():
    headers = login()
    book = create_book(headers)
    response = client.delete(f"/books/{book['id']}", headers=headers)
    assert response.status_code == 204
    assert client.get(f"/books/{book['id']}").status_code == 404
