from tests.helpers import create_book

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}

def test_response_has_request_id(client):
    response = client.get("/health")
    assert len(response.headers["X-Request-ID"]) == 16

def test_list_books_is_empty_at_start(client):
    response = client.get("/books")
    assert response.status_code == 200
    assert response.json()["total"] == 0  # 테스트마다 빈 데이터베이스이므로 항상 0입니다.

def test_get_missing_book_returns_404(client):
    response = client.get("/books/1")
    assert response.status_code == 404
    assert response.json()["code"] == "BOOK_NOT_FOUND"

def test_create_book(client, auth_headers, author_id):
    data = {"title": "테스트 도서", "author_id": author_id, "price": 15000, "isbn": "9790000000017", "stock": 2}
    response = client.post("/books", json=data, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "테스트 도서"
    assert body["stock"] == 2
    assert body["author"] == {"id": author_id, "name": "테스트 저자"}

def test_create_book_with_duplicate_isbn_returns_409(client, auth_headers, author_id):
    create_book(client, auth_headers, author_id, isbn="9790000000017")
    response = client.post("/books", headers=auth_headers,
                           json={"title": "다른 도서", "author_id": author_id, "price": 1000, "isbn": "9790000000017"})
    assert response.status_code == 409
    assert response.json()["code"] == "DUPLICATE_ISBN"

def test_get_book(client, auth_headers, author_id):
    book = create_book(client, auth_headers, author_id, title="조회 테스트")
    response = client.get(f"/books/{book['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "조회 테스트"

def test_update_book(client, auth_headers, author_id):
    book = create_book(client, auth_headers, author_id)
    response = client.patch(f"/books/{book['id']}", json={"price": 20000}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["price"] == 20000
    assert client.get(f"/books/{book['id']}").json()["price"] == 20000

def test_delete_book(client, auth_headers, author_id):
    book = create_book(client, auth_headers, author_id)
    response = client.delete(f"/books/{book['id']}", headers=auth_headers)
    assert response.status_code == 204
    assert client.get(f"/books/{book['id']}").status_code == 404
