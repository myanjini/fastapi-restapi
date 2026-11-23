from fastapi import FastAPI, HTTPException

app = FastAPI(title="도서 관리 API")

# 데이터베이스 대신 쓰는 임시 도서 목록입니다. 3장에서 데이터베이스로 바꿉니다.
BOOKS = [
    {"id": 1, "title": "파이썬 첫걸음", "author": "김하늘", "price": 18000},
    {"id": 2, "title": "웹 개발 입문", "author": "이도윤", "price": 22000},
    {"id": 3, "title": "데이터베이스 기초", "author": "김하늘", "price": 25000},
    {"id": 4, "title": "알기 쉬운 네트워크", "author": "박서준", "price": 20000},
]

@app.get("/")
def read_root():
    return {"message": "도서 관리 API에 오신 것을 환영합니다."}

@app.get("/health")
def health_check():
    # 서버가 요청에 응답할 수 있는지 확인하는 용도입니다.
    return {"status": "ok"}

@app.get("/books")
def list_books(author: str | None = None):
    # author가 없으면 전체 목록을, 있으면 그 저자의 도서만 돌려줍니다.
    if author is None:
        return BOOKS
    return [book for book in BOOKS if book["author"] == author]

@app.get("/books/{book_id}")
def get_book(book_id: int):
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    # 반복문을 다 돌아도 찾지 못하면 404 오류를 보냅니다.
    raise HTTPException(status_code=404, detail="도서를 찾을 수 없습니다.")
