from tests.helpers import create_book

def borrow(client, headers, book_id):
    return client.post("/loans", json={"book_id": book_id}, headers=headers)

def test_borrow_decreases_stock(client, auth_headers, author_id):
    book = create_book(client, auth_headers, author_id, stock=2)
    response = borrow(client, auth_headers, book["id"])
    assert response.status_code == 201
    assert client.get(f"/books/{book['id']}").json()["stock"] == 1

def test_borrow_out_of_stock_returns_409(client, auth_headers, author_id):
    book = create_book(client, auth_headers, author_id, stock=0)
    response = borrow(client, auth_headers, book["id"])
    assert response.status_code == 409
    assert response.json()["code"] == "OUT_OF_STOCK"

def test_borrow_same_book_twice_returns_409(client, auth_headers, author_id):
    book = create_book(client, auth_headers, author_id, stock=2)
    borrow(client, auth_headers, book["id"])
    response = borrow(client, auth_headers, book["id"])
    assert response.json()["code"] == "ALREADY_LOANED"

def test_return_others_loan_returns_403(client, make_user, author_id):
    user1 = make_user("user1@example.com")
    user2 = make_user("user2@example.com")
    book = create_book(client, user1, author_id, stock=1)
    loan = borrow(client, user1, book["id"]).json()
    response = client.post(f"/loans/{loan['id']}/return", headers=user2)
    assert response.status_code == 403

def test_return_twice_returns_409(client, auth_headers, author_id):
    book = create_book(client, auth_headers, author_id, stock=1)
    loan = borrow(client, auth_headers, book["id"]).json()
    first = client.post(f"/loans/{loan['id']}/return", headers=auth_headers)
    assert first.status_code == 200
    assert client.get(f"/books/{book['id']}").json()["stock"] == 1
    second = client.post(f"/loans/{loan['id']}/return", headers=auth_headers)
    assert second.json()["code"] == "ALREADY_RETURNED"
