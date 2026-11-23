from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="도서 관리 API")

# 데이터베이스 대신 쓰는 임시 도서 목록입니다. 3장에서 데이터베이스로 바꿉니다.
BOOKS = [
    {"id": 1, "title": "파이썬 첫걸음", "author": "김하늘", "price": 18000, "isbn": "9791100000011", "cost": 12000},
    {"id": 2, "title": "웹 개발 입문", "author": "이도윤", "price": 22000, "isbn": "9791100000028", "cost": 15000},
    {"id": 3, "title": "데이터베이스 기초", "author": "김하늘", "price": 25000, "isbn": None, "cost": 17000},
    {"id": 4, "title": "알기 쉬운 네트워크", "author": "박서준", "price": 20000, "isbn": None, "cost": 13000},
]

class BookCreate(BaseModel):
    """등록과 전체 수정(PUT)에 쓰는 입력 모델"""
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=50)
    price: int = Field(ge=0, le=1_000_000)
    isbn: str | None = Field(default=None, pattern=r"^\d{13}$")

class BookUpdate(BaseModel):
    """일부 수정(PATCH)에 쓰는 입력 모델. 모든 항목이 선택입니다."""
    title: str | None = Field(default=None, min_length=1, max_length=100)
    author: str | None = Field(default=None, min_length=1, max_length=50)
    price: int | None = Field(default=None, ge=0, le=1_000_000)
    isbn: str | None = Field(default=None, pattern=r"^\d{13}$")

class BookRead(BaseModel):
    """응답에 쓰는 출력 모델. 여기에 없는 필드는 응답에서 빠집니다."""
    id: int
    title: str
    author: str
    price: int
    isbn: str | None = None

@app.get("/")
def read_root():
    return {"message": "도서 관리 API에 오신 것을 환영합니다."}

@app.get("/health")
def health_check():
    return {"status": "ok"}

def find_book(book_id: int) -> dict:
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다.")

@app.get("/books", response_model=list[BookRead])
def list_books(author: str | None = None):
    if author is None:
        return BOOKS
    return [book for book in BOOKS if book["author"] == author]

@app.get("/books/{book_id}", response_model=BookRead)
def get_book(book_id: int):
    return find_book(book_id)

@app.post("/books", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(book_in: BookCreate):
    new_id = max(book["id"] for book in BOOKS) + 1 if BOOKS else 1
    book = {"id": new_id, **book_in.model_dump(), "cost": 0}
    BOOKS.append(book)
    return book

@app.put("/books/{book_id}", response_model=BookRead)
def replace_book(book_id: int, book_in: BookCreate):
    book = find_book(book_id)
    book.update(book_in.model_dump())
    return book

@app.patch("/books/{book_id}", response_model=BookRead)
def update_book(book_id: int, book_in: BookUpdate):
    book = find_book(book_id)
    # 보낸 항목만 꺼내고, null로 보낸 항목은 무시합니다.
    changes = book_in.model_dump(exclude_unset=True, exclude_none=True)
    book.update(changes)
    return book

@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int):
    book = find_book(book_id)
    BOOKS.remove(book)
