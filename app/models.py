from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # 비밀번호 원문이 아니라 해시만 저장합니다.
    hashed_password: Mapped[str] = mapped_column(String(255))
    # 역할: 일반 사용자는 "user", 관리자는 "admin"
    role: Mapped[str] = mapped_column(String(20), default="user")

class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    # 이 저자가 쓴 도서 목록. Book.author와 서로 연결됩니다.
    books: Mapped[list["Book"]] = relationship(back_populates="author")

class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    price: Mapped[int]
    isbn: Mapped[str | None] = mapped_column(String(13), unique=True)
    published_year: Mapped[int | None]  # 출간 연도. 기존 도서에는 값이 없으므로 None을 허용합니다.
    cover_url: Mapped[str | None] = mapped_column(String(200))  # 표지 이미지 주소

    # 테이블에 저장되는 열: 저자의 번호
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    # 파이썬에서 쓰는 속성: 저자 객체
    author: Mapped["Author"] = relationship(back_populates="books")

    # 도서를 등록한 사용자. 인증을 붙이기 전에 등록한 도서는 값이 없습니다.
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    # 재고 수량. 기존 도서는 0권으로 시작합니다.
    stock: Mapped[int] = mapped_column(default=0, server_default="0")
    # 이 도서의 재고 기록. 도서를 지우면 기록도 함께 지웁니다.
    stock_logs: Mapped[list["StockLog"]] = relationship(cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    # 토큰 원문이 아니라 SHA-256 해시(64글자)를 저장합니다.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime]  # 만료 시각(UTC)
    revoked: Mapped[bool] = mapped_column(default=False)  # True면 더는 쓸 수 없는 토큰

class StockLog(Base):
    """재고가 언제, 얼마나, 왜 바뀌었는지 남기는 기록입니다."""

    __tablename__ = "stock_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    change: Mapped[int]  # 늘어나면 양수, 줄어들면 음수
    reason: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())  # 데이터베이스가 현재 시각을 넣습니다.

class Loan(Base):
    """누가 어떤 도서를 언제 빌리고 반납했는지 기록합니다."""

    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    loaned_at: Mapped[datetime] = mapped_column(server_default=func.now())
    returned_at: Mapped[datetime | None]  # 반납하기 전에는 None

    book: Mapped["Book"] = relationship()

class LoginFailure(Base):
    """로그인 실패 기록. 일정 시간 안의 실패 횟수를 세는 데 씁니다."""

    __tablename__ = "login_failures"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    ip: Mapped[str] = mapped_column(String(45), index=True)  # IPv6 주소까지 담을 수 있는 길이
    created_at: Mapped[datetime] = mapped_column(index=True)
