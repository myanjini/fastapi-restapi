from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import AppError
from app.routers import books

app = FastAPI(
    title="도서 관리 API",
    description="도서를 등록하고 조회, 수정, 삭제하는 API입니다.",
    version="0.1.0",
)

@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    # 어떤 AppError든 같은 모양의 JSON으로 바꿔 응답합니다.
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )

@app.get("/", tags=["기본"])
def read_root():
    return {"message": "도서 관리 API에 오신 것을 환영합니다."}

@app.get("/health", tags=["기본"])
def health_check():
    return {"status": "ok"}

app.include_router(books.router)
