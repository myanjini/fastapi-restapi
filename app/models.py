from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

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

    # 테이블에 저장되는 열: 저자의 번호
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    # 파이썬에서 쓰는 속성: 저자 객체
    author: Mapped["Author"] = relationship(back_populates="books")
