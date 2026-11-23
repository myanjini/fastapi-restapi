import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.errors import AppError
from app.routers import books

app = FastAPI(
    title=settings.app_name,
    description="도서를 등록하고 조회, 수정, 삭제하는 API입니다.",
    version="0.1.0",
)

# 이 주소에서 실행되는 웹 화면만 브라우저에서 이 API를 호출할 수 있습니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)  # 실제 경로 함수가 여기서 실행됩니다.
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{elapsed_ms:.1f}ms"
    print(f"{request.method} {request.url.path} {response.status_code} {elapsed_ms:.1f}ms")
    return response

@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    # 어떤 AppError든 같은 모양의 JSON으로 바꿔 응답합니다.
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )

@app.get("/", tags=["기본"])
def read_root():
    return {"message": f"{settings.app_name}에 오신 것을 환영합니다."}

@app.get("/health", tags=["기본"])
def health_check():
    return {"status": "ok"}

app.include_router(books.router)
