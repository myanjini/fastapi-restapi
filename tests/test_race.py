"""동시성 문제가 다시 생기지 않는지 확인하는 테스트"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.errors import AppError
from app.models import Book, Loan
from app.services.books import change_stock
from tests.helpers import create_book

def test_stale_stock_cannot_be_oversold(client, db_session, make_user, author_id):
    user1 = make_user("user1@example.com")
    user2 = make_user("user2@example.com")
    book = create_book(client, user1, author_id, stock=1)

    stale = db_session.get(Book, book["id"])  # 재고가 1권일 때 읽어 둔 객체: 늦게 도착한 요청을 흉내 냅니다.
    assert stale.stock == 1
    assert client.post("/loans", json={"book_id": book["id"]}, headers=user2).status_code == 201  # 다른 요청이 먼저 빌림

    with pytest.raises(AppError) as error:
        change_stock(db_session, stale, -1, "대여")  # 낡은 값(1)을 믿고 재고를 줄이려 합니다.
    assert error.value.code == "INSUFFICIENT_STOCK"
    db_session.rollback()
    assert client.get(f"/books/{book['id']}").json()["stock"] == 0

def test_only_one_active_loan_per_user_and_book(client, db_session, auth_headers, author_id):
    book = create_book(client, auth_headers, author_id, stock=5)
    assert client.post("/loans", json={"book_id": book["id"]}, headers=auth_headers).status_code == 201
    user_id = client.get("/auth/me", headers=auth_headers).json()["id"]

    db_session.add(Loan(user_id=user_id, book_id=book["id"]))  # 서비스의 검사를 건너뛰고 같은 대여를 한 번 더 넣어 봅니다.
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
