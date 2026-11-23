import pytest

from tests.helpers import create_book

def test_signup_does_not_return_password(client):
    response = client.post("/auth/signup", json={"email": "new@example.com", "password": "test-pass-123"})
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "password" not in body and "hashed_password" not in body

def test_signup_with_duplicate_email_returns_409(client):
    client.post("/auth/signup", json={"email": "dup@example.com", "password": "test-pass-123"})
    response = client.post("/auth/signup", json={"email": "DUP@example.com", "password": "test-pass-123"})
    assert response.status_code == 409

def test_login_with_wrong_password_returns_401(client, make_user):
    make_user("user1@example.com")
    response = client.post("/auth/token", data={"username": "user1@example.com", "password": "wrong-pass"})
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"

def test_me_with_token(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "tester@example.com"

@pytest.mark.parametrize("headers, code", [
    ({}, "NOT_AUTHENTICATED"),                                     # 헤더 없음
    ({"Authorization": "Bearer abc.def.ghi"}, "INVALID_TOKEN"),    # 위조한 토큰
])
def test_create_book_without_valid_token_returns_401(client, author_id, headers, code):
    response = client.post("/books", json={"title": "x", "author_id": author_id, "price": 1}, headers=headers)
    assert response.status_code == 401
    assert response.json()["code"] == code

def test_update_others_book_returns_403(client, make_user, author_id):
    owner = make_user("owner@example.com")
    other = make_user("other@example.com")
    book = create_book(client, owner, author_id)
    response = client.patch(f"/books/{book['id']}", json={"price": 1}, headers=other)
    assert response.status_code == 403

def test_admin_can_update_others_book(client, make_user, author_id):
    owner = make_user("owner@example.com")
    admin = make_user("admin@example.com", role="admin")
    book = create_book(client, owner, author_id)
    response = client.patch(f"/books/{book['id']}", json={"price": 1}, headers=admin)
    assert response.status_code == 200

def test_refresh_token_can_be_used_only_once(client, make_user):
    make_user("user1@example.com")
    tokens = client.post("/auth/token", data={"username": "user1@example.com", "password": "test-pass-123"}).json()

    first = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert first.status_code == 200
    assert first.json()["refresh_token"] != tokens["refresh_token"]

    second = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert second.status_code == 401

def test_logout_blocks_refresh(client, make_user):
    make_user("user1@example.com")
    tokens = client.post("/auth/token", data={"username": "user1@example.com", "password": "test-pass-123"}).json()
    assert client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}).status_code == 204
    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 401
