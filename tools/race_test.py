"""동시 대여 시험: 재고가 1권인 도서를 10명이 동시에 빌립니다. 사용법: python tools/race_test.py 도서번호"""
import sys
from concurrent.futures import ThreadPoolExecutor

import httpx

BASE_URL = "http://127.0.0.1:8000"
BOOK_ID = int(sys.argv[1])
PASSWORD = "race-test-pass-1"

def login(i: int) -> dict:
    email = f"race{i}@example.com"
    httpx.post(f"{BASE_URL}/auth/signup", json={"email": email, "password": PASSWORD})  # 이미 있으면 409, 무시
    token = httpx.post(f"{BASE_URL}/auth/token", data={"username": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def borrow(headers: dict) -> int:
    return httpx.post(f"{BASE_URL}/loans", json={"book_id": BOOK_ID}, headers=headers, timeout=30).status_code

users = [login(i) for i in range(10)]           # 먼저 10명이 모두 로그인해 둡니다.
with ThreadPoolExecutor(max_workers=10) as pool:  # 10개의 요청을 한꺼번에 보냅니다.
    results = list(pool.map(borrow, users))

print("응답 상태:", results)
print("대여 성공(201):", results.count(201))
print("남은 재고:", httpx.get(f"{BASE_URL}/books/{BOOK_ID}").json()["stock"])
