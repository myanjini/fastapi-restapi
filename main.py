from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="도서 관리 API",
    description="도서를 등록하고 조회, 수정, 삭제하는 API입니다.",
    version="0.1.0",
)

BOOKS = [
    {"id": 1, "title": "파이썬 첫걸음", "author": "김하늘", "price": 18000, "isbn": "9791100000011", "cost": 12000},
    {"id": 2, "title": "웹 개발 입문", "author": "이도윤", "price": 22000, "isbn": "9791100000028", "cost": 15000},
    {"id": 3, "title": "데이터베이스 기초", "author": "김하늘", "price": 25000, "isbn": None, "cost": 17000},
    {"id": 4, "title": "알기 쉬운 네트워크", "author": "박서준", "price": 20000, "isbn": None, "cost": 13000},
]

class AppError(Exception):
    """이 앱이 일부러 보내는 오류. 상태 코드, 오류 코드, 메시지를 담습니다."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message

@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    # 어떤 AppError든 같은 모양의 JSON으로 바꿔 응답합니다.
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )

class BookCreate(BaseModel):
    """등록과 전체 수정(PUT)에 쓰는 입력 모델"""
    title: str = Field(min_length=1, max_length=100, examples=["FastAPI 실전"])
    author: str = Field(min_length=1, max_length=50, examples=["최유나"])
    price: int = Field(ge=0, le=1_000_000, examples=[27000])
    isbn: str | None = Field(default=None, pattern=r"^\d{13}$", examples=["9791100000035"])

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

@app.get("/", tags=["기본"])
def read_root():
    return {"message": "도서 관리 API에 오신 것을 환영합니다."}

@app.get("/health", tags=["기본"])
def health_check():
    return {"status": "ok"}

def find_book(book_id: int) -> dict:
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    raise AppError(404, "BOOK_NOT_FOUND", f"{book_id}번 도서를 찾을 수 없습니다.")

def check_isbn_unique(isbn: str | None, exclude_id: int | None = None) -> None:
    """같은 ISBN이 이미 있으면 409 오류를 냅니다. 수정할 때는 자기 자신을 빼고 비교합니다."""
    if isbn is None:
        return
    for book in BOOKS:
        if book["isbn"] == isbn and book["id"] != exclude_id:
            raise AppError(409, "DUPLICATE_ISBN", "이미 등록된 ISBN입니다.")

@app.get("/books", response_model=list[BookRead], tags=["도서"], summary="도서 목록 조회")
def list_books(author: str | None = None):
    """저자 이름(author)을 주면 그 저자의 도서만 돌려줍니다."""
    if author is None:
        return BOOKS
    return [book for book in BOOKS if book["author"] == author]

@app.get("/books/{book_id}", response_model=BookRead, tags=["도서"], summary="도서 상세 조회",
         responses={404: {"description": "도서를 찾을 수 없음"}})
def get_book(book_id: int):
    return find_book(book_id)

@app.post("/books", response_model=BookRead, status_code=status.HTTP_201_CREATED, tags=["도서"],
          summary="도서 등록", responses={409: {"description": "이미 등록된 ISBN"}})
def create_book(book_in: BookCreate):
    check_isbn_unique(book_in.isbn)
    new_id = max(book["id"] for book in BOOKS) + 1 if BOOKS else 1
    book = {"id": new_id, **book_in.model_dump(), "cost": 0}
    BOOKS.append(book)
    return book

@app.put("/books/{book_id}", response_model=BookRead, tags=["도서"], summary="도서 전체 수정")
def replace_book(book_id: int, book_in: BookCreate):
    book = find_book(book_id)
    check_isbn_unique(book_in.isbn, exclude_id=book_id)
    book.update(book_in.model_dump())
    return book

@app.patch("/books/{book_id}", response_model=BookRead, tags=["도서"], summary="도서 일부 수정")
def update_book(book_id: int, book_in: BookUpdate):
    book = find_book(book_id)
    changes = book_in.model_dump(exclude_unset=True, exclude_none=True)
    check_isbn_unique(changes.get("isbn"), exclude_id=book_id)
    book.update(changes)
    return book

@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["도서"], summary="도서 삭제")
def delete_book(book_id: int):
    book = find_book(book_id)
    BOOKS.remove(book)
