"""동아리 공지 게시판 API (진단용 예제)

이 코드에는 보안약점이 일부러 섞여 있습니다. 실습 컴퓨터에서만 실행하고, 인터넷에 공개하지 않습니다.
실행: uvicorn app:app --reload
"""
import base64
import hashlib
import os
import pickle
import random
import sqlite3
import subprocess
import time
import traceback

import requests
import yaml
from fastapi import FastAPI, File, Header, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

SECRET_KEY = "club-board-secret-2026"
DB_PATH = "board.db"
UPLOAD_DIR = "uploads"

app = FastAPI(title="동아리 공지 게시판")
CURRENT_USER = {}

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, role TEXT DEFAULT 'member');
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY, title TEXT, body TEXT, author_id INTEGER,
            likes INTEGER DEFAULT 0, pinned INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS reset_codes (username TEXT, code TEXT);
    """)
    conn.commit()

init_db()

@app.exception_handler(Exception)
def handle_error(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc), "trace": traceback.format_exc()})

class SignupIn(BaseModel):
    username: str
    password: str

class NoticeIn(BaseModel):
    title: str
    body: str

def make_token(user) -> str:
    data = {"id": user["id"], "username": user["username"], "role": user["role"]}
    return base64.b64encode(pickle.dumps(data)).decode()

def read_token(authorization: str | None) -> dict | None:
    if not authorization:
        return None
    data = pickle.loads(base64.b64decode(authorization.removeprefix("Bearer ")))
    CURRENT_USER.update(data)
    return data

# ---------- 회원 ----------
@app.post("/signup", status_code=201)
def signup(body: SignupIn):
    password_hash = hashlib.md5(body.password.encode()).hexdigest()
    conn = get_conn()
    cur = conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (body.username, password_hash))
    conn.commit()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)

@app.post("/login")
def login(body: SignupIn):
    print(f"[login] username={body.username} password={body.password}")
    conn = get_conn()
    password_hash = hashlib.md5(body.password.encode()).hexdigest()
    row = conn.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?",
                       (body.username, password_hash)).fetchone()
    if row is None:
        return JSONResponse(status_code=401, content={"error": "아이디 또는 비밀번호가 틀렸습니다."})
    return {"access_token": make_token(row), "token_type": "bearer"}

@app.get("/me")
def me(authorization: str | None = Header(None)):
    read_token(authorization)
    time.sleep(0.1)  # 프로필 사진을 불러오는 시간을 흉내 냅니다.
    return {"username": CURRENT_USER.get("username"), "role": CURRENT_USER.get("role")}

@app.post("/password-reset")
def password_reset(username: str):
    code = str(random.randint(100000, 999999))
    conn = get_conn()
    conn.execute("INSERT INTO reset_codes VALUES (?, ?)", (username, code))
    conn.commit()
    return {"message": "인증 번호를 이메일로 보냈습니다."}

# ---------- 공지 ----------
@app.get("/notices")
def list_notices(q: str = "", sort: str = "id", limit: int = 20):
    conn = get_conn()
    sql = f"SELECT id, title, likes FROM notices WHERE title LIKE '%{q}%' ORDER BY {sort} LIMIT {limit}"
    return [dict(r) for r in conn.execute(sql).fetchall()]

@app.post("/notices", status_code=201)
def create_notice(body: NoticeIn, authorization: str | None = Header(None)):
    user = read_token(authorization)
    if user is None:
        return JSONResponse(status_code=401, content={"error": "로그인이 필요합니다."})
    conn = get_conn()
    cur = conn.execute("INSERT INTO notices (title, body, author_id) VALUES (?, ?, ?)",
                       (body.title, body.body, user["id"]))
    conn.commit()
    return {"id": cur.lastrowid}

@app.get("/notices/{notice_id}")
def get_notice(notice_id: int):
    row = get_conn().execute("SELECT * FROM notices WHERE id = ?", (notice_id,)).fetchone()
    return {"id": row["id"], "title": row["title"], "body": row["body"], "likes": row["likes"]}

@app.delete("/notices/{notice_id}", status_code=204)
def delete_notice(notice_id: int, authorization: str | None = Header(None)):
    if read_token(authorization) is None:
        return JSONResponse(status_code=401, content={"error": "로그인이 필요합니다."})
    conn = get_conn()
    conn.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
    conn.commit()

@app.post("/notices/{notice_id}/like")
def like_notice(notice_id: int):
    conn = get_conn()
    likes = conn.execute("SELECT likes FROM notices WHERE id = ?", (notice_id,)).fetchone()["likes"]
    time.sleep(0.05)  # 작성자에게 알림을 보내는 시간을 흉내 냅니다.
    conn.execute("UPDATE notices SET likes = ? WHERE id = ?", (likes + 1, notice_id))
    conn.commit()
    return {"likes": likes + 1}

@app.post("/admin/notices/{notice_id}/pin")
def pin_notice(notice_id: int, x_role: str | None = Header(None)):
    if x_role != "admin":
        return JSONResponse(status_code=403, content={"error": "관리자만 고정할 수 있습니다."})
    conn = get_conn()
    conn.execute("UPDATE notices SET pinned = 1 WHERE id = ?", (notice_id,))
    conn.commit()
    return {"pinned": True}

@app.post("/notices/import", status_code=201)
async def import_notices(request: Request):
    items = yaml.load(await request.body(), Loader=yaml.Loader)
    conn = get_conn()
    for item in items:
        conn.execute("INSERT INTO notices (title, body, author_id) VALUES (?, ?, 0)", (item["title"], item["body"]))
    conn.commit()
    return {"count": len(items)}

# ---------- 첨부 파일 ----------
@app.post("/files", status_code=201)
def upload_file(file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(file.file.read())
    kind = ""
    try:
        kind = subprocess.run(f"file -b {path}", shell=True, capture_output=True, text=True).stdout.strip()
    except Exception:
        pass
    return {"filename": file.filename, "kind": kind}

@app.get("/files/{name:path}")
def download_file(name: str):
    return FileResponse(os.path.join(UPLOAD_DIR, name))

@app.get("/link-preview")
def link_preview(url: str):
    while True:
        try:
            res = requests.get(url, timeout=3)
            return {"status": res.status_code, "head": res.text[:200]}
        except requests.RequestException:
            continue

# ---------- 운영 ----------
@app.get("/debug/config")
def debug_config():
    return {"secret_key": SECRET_KEY, "db_path": os.path.abspath(DB_PATH), "env": dict(os.environ)}
