from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="도서 관리 API")

# 데이터베이스 대신 쓰는 임시 도서 목록입니다. 3장에서 데이터베이스로 바꿉니다.
BOOKS = [
    {"id": 1, "title": "파이썬 첫걸음", "author": "김하늘", "price": 18000},
    {"id": 2, "title": "웹 개발 입문", "author": "이도윤", "price": 22000},
    {"id": 3, "title": "데이터베이스 기초", "author": "김하늘", "price": 25000},
    {"id": 4, "title": "알기 쉬운 네트워크", "author": "박서준", "price": 20000},
]

class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=50)
    price: int = Field(ge=0, le=1_000_000)

@app.get("/")
def read_root():
    return {"message": "도서 관리 API에 오신 것을 환영합니다."}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/books")
def list_books(author: str | None = None):
    if author is None:
        return BOOKS
    return [book for book in BOOKS if book["author"] == author]

@app.get("/books/{book_id}")
def get_book(book_id: int):
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다.")

@app.post("/books")
def create_book(book_in: BookCreate):
    new_id = max(book["id"] for book in BOOKS) + 1 if BOOKS else 1
    book = {"id": new_id, **book_in.model_dump()}
    BOOKS.append(book)
    return book
