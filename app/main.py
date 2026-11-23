import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.dependencies import SessionDep
from app.errors import AppError
from app.logging_config import request_id_var, setup_logging
from app.routers import auth, authors, books, files, loans, reports
from app.services.covers import COVER_DIR

setup_logging(settings.log_level)

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

logger = logging.getLogger("app.request")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id_var.set(uuid.uuid4().hex[:16])  # 이 요청에서 남기는 모든 로그에 같은 ID가 붙습니다.
    start = time.perf_counter()
    info = {"method": request.method, "path": request.url.path}
    try:
        response = await call_next(request)  # 실제 경로 함수가 여기서 실행됩니다.
    except Exception:
        info["duration_ms"] = round((time.perf_counter() - start) * 1000, 1)
        logger.exception("처리하지 못한 오류", extra={**info, "status": 500})
        raise  # 응답은 FastAPI의 기본 처리에 맡깁니다. 보안 단원에서 안전한 오류 응답으로 바꿉니다.
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    response.headers["X-Request-ID"] = request_id_var.get()
    response.headers["X-Process-Time"] = f"{duration_ms}ms"
    logger.info("요청 처리", extra={**info, "status": response.status_code, "duration_ms": duration_ms})
    return response

@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    # 어떤 AppError든 같은 모양의 JSON으로 바꿔 응답합니다.
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
        headers=exc.headers,
    )

@app.get("/", tags=["기본"])
def read_root():
    return {"message": f"{settings.app_name}에 오신 것을 환영합니다."}

@app.get("/health", tags=["기본"])
def health_check(db: SessionDep):
    try:
        db.execute(text("SELECT 1"))  # 데이터베이스에 가장 가벼운 질의를 보내 봅니다.
    except SQLAlchemyError:
        logger.exception("데이터베이스 연결 확인 실패")
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})
    return {"status": "ok", "database": "ok"}

app.include_router(auth.router)
app.include_router(authors.router)
app.include_router(books.router)
app.include_router(loans.router)
app.include_router(reports.router)
app.include_router(files.router)

# 올린 표지 파일을 /covers/파일이름 주소로 내보냅니다.
COVER_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/covers", StaticFiles(directory=COVER_DIR), name="covers")
