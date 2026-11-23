"""동아리 공지 게시판 API (조치 완료 예시)

진단용 예제의 보안약점을 조치한 코드입니다. 주석의 [번호]는 예시 진단표의 번호입니다.
실행: SECRET_KEY 환경 변수를 32자 이상으로 정한 뒤 uvicorn app:app --reload
"""
import hashlib
import logging
import os
import secrets
import sqlite3
import subprocess
import time
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import jwt
import requests
import yaml
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pwdlib import PasswordHash
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("board")

SECRET_KEY = os.environ.get("SECRET_KEY", "")  # [11] 비밀 키는 코드 밖(환경 변수)에서 받습니다.
if len(SECRET_KEY) < 32:
    raise RuntimeError("SECRET_KEY 환경 변수를 32자 이상으로 정하세요.")
DB_PATH = "board.db"
UPLOAD_DIR = Path("uploads").resolve()
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".png", ".jpg"}
MAX_FILE_SIZE = 2 * 1024 * 1024
PREVIEW_HOSTS = {"example.com", "www.example.com"}  # 미리 보기를 허용하는 사이트만 적습니다.
MAX_FAILURES, FAILURE_WINDOW = 5, 15 * 60
login_failures: dict[str, list[float]] = {}  # 예제를 짧게 하려고 메모리에 둡니다. 실제 서비스는 데이터베이스에 둡니다.

app = FastAPI(title="동아리 공지 게시판")
password_hash = PasswordHash.recommended()  # [8] Argon2(솔트를 자동으로 붙입니다.)

def get_db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()  # [19] 요청이 끝나면 성공하든 실패하든 연결을 닫습니다.

def init_db():
    UPLOAD_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'member');
            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY, title TEXT, body TEXT, author_id INTEGER,
                likes INTEGER DEFAULT 0, pinned INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS reset_codes (username TEXT, code_hash TEXT);
        """)
        conn.commit()
    finally:
        conn.close()

init_db()

@app.exception_handler(Exception)
def handle_error(request: Request, exc: Exception):
    logger.exception("처리하지 못한 오류")  # [16] 자세한 내용은 서버 로그에만 남깁니다.
    return JSONResponse(status_code=500, content={"error": "서버 오류가 발생했습니다."})

class SignupIn(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    password: str = Field(min_length=10, max_length=128)  # [9] 10자 이상만 받습니다.

class LoginIn(BaseModel):
    username: str = Field(max_length=30)
    password: str = Field(max_length=128)

class NoticeIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=5000)

# ---------- 토큰 ----------
def make_token(user) -> str:
    payload = {"sub": str(user["id"]), "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")  # [20] 서명한 JWT를 씁니다.

def current_user(authorization: str | None = Header(None), db: sqlite3.Connection = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "로그인이 필요합니다.")
    try:
        payload = jwt.decode(authorization.removeprefix("Bearer "), SECRET_KEY, algorithms=["HS256"],
                             options={"require": ["exp", "sub"]})
    except jwt.InvalidTokenError:
        raise HTTPException(401, "토큰이 올바르지 않습니다.")
    user = db.execute("SELECT id, username, role FROM users WHERE id = ?", (int(payload["sub"]),)).fetchone()
    if user is None:
        raise HTTPException(401, "토큰이 올바르지 않습니다.")
    return dict(user)  # [22] 요청마다 새로 만든 값을 돌려줍니다. 전역 변수에 담지 않습니다.

def require_admin(user: dict = Depends(current_user)) -> dict:
    if user["role"] != "admin":  # [6] 서버가 확인한 역할로만 판단합니다.
        raise HTTPException(403, "관리자만 할 수 있습니다.")
    return user

# ---------- 회원 ----------
@app.post("/signup", status_code=201)
def signup(body: SignupIn, db: sqlite3.Connection = Depends(get_db)):
    if body.username in body.password:
        raise HTTPException(422, "비밀번호에 아이디를 넣을 수 없습니다.")
    try:
        cur = db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                         (body.username, password_hash.hash(body.password)))
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "이미 쓰고 있는 아이디입니다.")
    return {"id": cur.lastrowid, "username": body.username}  # [21] 해시는 응답에 넣지 않습니다.

def check_failures(username: str) -> None:
    now = time.monotonic()
    recent = [t for t in login_failures.get(username, []) if now - t < FAILURE_WINDOW]
    login_failures[username] = recent
    if len(recent) >= MAX_FAILURES:  # [10] 비밀번호를 확인하기 전에 막습니다.
        raise HTTPException(429, "로그인 실패가 많습니다. 15분 뒤에 다시 시도하세요.", headers={"Retry-After": "900"})

@app.post("/login")
def login(body: LoginIn, db: sqlite3.Connection = Depends(get_db)):
    check_failures(body.username)  # [23] 비밀번호를 출력하던 디버그 코드는 지웠습니다.
    row = db.execute("SELECT * FROM users WHERE username = ?", (body.username,)).fetchone()
    if row is None or not password_hash.verify(body.password, row["password_hash"]):
        login_failures.setdefault(body.username, []).append(time.monotonic())
        raise HTTPException(401, "아이디 또는 비밀번호가 틀렸습니다.")
    login_failures.pop(body.username, None)
    return {"access_token": make_token(row), "token_type": "bearer"}

@app.get("/me")
def me(user: dict = Depends(current_user)):
    time.sleep(0.1)  # 프로필 사진을 불러오는 시간을 흉내 냅니다.
    return {"username": user["username"], "role": user["role"]}

@app.post("/password-reset")
def password_reset(username: str, db: sqlite3.Connection = Depends(get_db)):
    code = f"{secrets.randbelow(1_000_000):06d}"  # [12] 추측할 수 없는 난수를 씁니다.
    db.execute("INSERT INTO reset_codes VALUES (?, ?)", (username, hashlib.sha256(code.encode()).hexdigest()))
    db.commit()
    return {"message": "인증 번호를 이메일로 보냈습니다."}

# ---------- 공지 ----------
SORT_COLUMNS = {"id": "id", "likes": "likes DESC"}

@app.get("/notices")
def list_notices(q: str = Query("", max_length=100), sort: Literal["id", "likes"] = "id",
                 limit: int = Query(20, ge=1, le=100), db: sqlite3.Connection = Depends(get_db)):
    # [1] 값은 ? 자리에 따로 넘기고, 정렬 열은 허용 목록에서만 고릅니다.
    sql = f"SELECT id, title, likes FROM notices WHERE title LIKE ? ORDER BY {SORT_COLUMNS[sort]} LIMIT ?"  # nosec B608
    return [dict(r) for r in db.execute(sql, (f"%{q}%", limit)).fetchall()]

@app.post("/notices", status_code=201)
def create_notice(body: NoticeIn, user: dict = Depends(current_user), db: sqlite3.Connection = Depends(get_db)):
    cur = db.execute("INSERT INTO notices (title, body, author_id) VALUES (?, ?, ?)", (body.title, body.body, user["id"]))
    db.commit()
    return {"id": cur.lastrowid}

def find_notice(db: sqlite3.Connection, notice_id: int):
    row = db.execute("SELECT * FROM notices WHERE id = ?", (notice_id,)).fetchone()
    if row is None:  # [18] 결과가 없을 때를 먼저 처리합니다.
        raise HTTPException(404, "공지를 찾을 수 없습니다.")
    return row

@app.get("/notices/{notice_id}")
def get_notice(notice_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = find_notice(db, notice_id)
    return {"id": row["id"], "title": row["title"], "body": row["body"], "likes": row["likes"]}

@app.delete("/notices/{notice_id}", status_code=204)
def delete_notice(notice_id: int, user: dict = Depends(current_user), db: sqlite3.Connection = Depends(get_db)):
    row = find_notice(db, notice_id)
    if row["author_id"] != user["id"] and user["role"] != "admin":  # [7] 작성자나 관리자만 지웁니다.
        raise HTTPException(404, "공지를 찾을 수 없습니다.")
    db.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
    db.commit()

@app.post("/notices/{notice_id}/like")
def like_notice(notice_id: int, db: sqlite3.Connection = Depends(get_db)):
    # [14] 읽고 더해서 쓰는 대신, 데이터베이스가 한 문장으로 더합니다.
    row = db.execute("UPDATE notices SET likes = likes + 1 WHERE id = ? RETURNING likes", (notice_id,)).fetchone()
    db.commit()
    if row is None:
        raise HTTPException(404, "공지를 찾을 수 없습니다.")
    time.sleep(0.05)  # 작성자에게 알림을 보내는 시간을 흉내 냅니다.
    return {"likes": row["likes"]}

@app.post("/admin/notices/{notice_id}/pin")
def pin_notice(notice_id: int, admin: dict = Depends(require_admin), db: sqlite3.Connection = Depends(get_db)):
    find_notice(db, notice_id)
    db.execute("UPDATE notices SET pinned = 1 WHERE id = ?", (notice_id,))
    db.commit()
    return {"pinned": True}

@app.post("/notices/import", status_code=201)
async def import_notices(request: Request, admin: dict = Depends(require_admin), db: sqlite3.Connection = Depends(get_db)):
    # [13] 공지를 한꺼번에 넣는 기능은 관리자만 씁니다.
    try:
        data = yaml.safe_load(await request.body())  # [24] 기본 자료형만 만드는 safe_load를 씁니다.
        items = [NoticeIn.model_validate(item) for item in data]
    except (yaml.YAMLError, ValidationError, TypeError):
        raise HTTPException(400, "가져올 공지 형식이 올바르지 않습니다.")
    for item in items:
        db.execute("INSERT INTO notices (title, body, author_id) VALUES (?, ?, ?)", (item.title, item.body, admin["id"]))
    db.commit()
    return {"count": len(items)}

# ---------- 첨부 파일 ----------
@app.post("/files", status_code=201)
def upload_file(file: UploadFile = File(...), user: dict = Depends(current_user)):  # [13] 로그인한 사용자만
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:  # [4] 허용한 확장자만 받습니다.
        raise HTTPException(400, "올릴 수 없는 파일 형식입니다.")
    data = file.file.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(413, "파일 크기는 2MB를 넘을 수 없습니다.")
    saved = f"{uuid.uuid4().hex}{ext}"  # [2] 저장 이름은 서버가 만듭니다.
    path = UPLOAD_DIR / saved
    path.write_bytes(data)
    try:
        # [3] 셸을 거치지 않고, 명령과 인자를 목록으로 넘깁니다.
        kind = subprocess.run(["file", "-b", str(path)], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        logger.warning("파일 형식을 확인하지 못했습니다: %s", saved)  # [17] 실패를 기록하고 알 수 없음으로 둡니다.
        kind = "unknown"
    return {"filename": saved, "kind": kind}

@app.get("/files/{name}")
def download_file(name: str):
    path = (UPLOAD_DIR / name).resolve()
    if not path.is_relative_to(UPLOAD_DIR) or not path.is_file():  # [2] 업로드 폴더 밖은 열지 않습니다.
        raise HTTPException(404, "파일을 찾을 수 없습니다.")
    return FileResponse(path)

@app.get("/link-preview")
def link_preview(url: str = Query(max_length=300), user: dict = Depends(current_user)):  # [13] 로그인한 사용자만
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in PREVIEW_HOSTS:  # [5] 허용한 사이트만 요청합니다.
        raise HTTPException(400, "미리 볼 수 없는 주소입니다.")
    for _ in range(3):  # [15] 다시 시도하는 횟수에 끝을 둡니다.
        try:
            res = requests.get(url, timeout=3, allow_redirects=False)
            return {"status": res.status_code, "head": res.text[:200]}
        except requests.RequestException:
            time.sleep(0.5)
    raise HTTPException(502, "주소에 연결하지 못했습니다.")

# [23] 설정과 비밀 키를 보여 주던 /debug/config는 지웠습니다.
