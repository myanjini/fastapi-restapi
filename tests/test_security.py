"""게시판 API 보안 테스트

테스트 이름 앞의 숫자는 예시 진단표(11.10절)의 번호입니다. 조치하기 전의 app.py에서는 모두 실패하고,
조치를 마치면 모두 통과해야 합니다. 테스트를 고쳐서 통과시키지 않습니다. 고치는 것은 app.py뿐입니다.
"""
import base64
import hashlib
import importlib
import os
import pickle
import random
import sqlite3
import sys
import threading

import pytest
import requests

SQLI = "%' UNION SELECT id, username, password_hash FROM users --"


def run_together(count: int, work):
    """스레드 count개를 모두 준비시킨 뒤 한꺼번에 출발시키고, 결과를 순서대로 돌려줍니다."""
    barrier = threading.Barrier(count)
    results = [None] * count

    def runner(i):
        barrier.wait()
        results[i] = work(i)

    threads = [threading.Thread(target=runner, args=(i,)) for i in range(count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    return results


class MkdirOnLoad:
    """되살릴 때 os.mkdir을 부르는 객체. 해가 없는 함수로 코드 실행 여부만 확인합니다."""

    def __init__(self, name: str):
        self.name = name

    def __reduce__(self):
        return (os.mkdir, (self.name,))


# ---------- 입력데이터 검증 및 표현 ----------
def test_01_search_sql_injection_does_not_leak_users(client, login, notice):
    res = client.get("/notices", params={"q": SQLI})
    assert res.status_code == 200
    assert "alice" not in res.text  # 사용자 이름과 해시가 공지 목록에 섞여 나오면 안 됩니다.


def test_01_sort_accepts_only_allowed_values(client, notice):
    res = client.get("/notices", params={"sort": "(SELECT password_hash FROM users)"})
    assert res.status_code == 422


def test_02_download_cannot_leave_upload_folder(client, notice):
    res = client.get("/files/%2e%2e%2fboard.db")
    assert res.status_code == 404
    assert b"SQLite format" not in res.content


def test_02_upload_name_cannot_leave_upload_folder(client, login, tmp_path):
    headers = login("alice")
    client.post("/files", files={"file": ("../escaped.txt", b"hello")}, headers=headers)
    assert not (tmp_path / "escaped.txt").exists()  # 업로드 폴더 밖에 파일이 생기면 안 됩니다.


def test_03_upload_name_is_not_a_shell_command(client, login, tmp_path):
    headers = login("alice")
    client.post("/files", files={"file": ("memo.txt;mkdir injected;#.txt", b"hello")}, headers=headers)
    assert not (tmp_path / "injected").exists()  # 파일 이름 속의 명령이 실행되면 안 됩니다.


def test_04_upload_rejects_dangerous_extension(client, login):
    headers = login("alice")
    res = client.post("/files", files={"file": ("page.html", b"<script>alert(1)</script>")}, headers=headers)
    assert res.status_code == 400


def test_05_preview_rejects_internal_address(client, login, monkeypatch):
    called = []
    monkeypatch.setattr(requests, "get", lambda url, **kw: called.append(url))
    headers = login("alice")
    res = client.get("/link-preview", params={"url": "https://169.254.169.254/latest/meta-data/"}, headers=headers)
    assert res.status_code == 400
    assert called == []  # 서버가 내부 주소로 요청을 보내면 안 됩니다.


# ---------- 보안기능 ----------
def test_06_role_header_does_not_make_admin(client, login, notice):
    headers = {**login("bob"), "X-Role": "admin"}
    res = client.post(f"/admin/notices/{notice}/pin", headers=headers)
    assert res.status_code in (401, 403)
    with sqlite3.connect("board.db") as conn:
        assert conn.execute("SELECT pinned FROM notices WHERE id = ?", (notice,)).fetchone()[0] == 0


def test_07_cannot_delete_others_notice(client, login, notice):
    headers = login("bob")
    res = client.delete(f"/notices/{notice}", headers=headers)
    assert res.status_code == 404
    assert client.get(f"/notices/{notice}").status_code == 200  # 공지가 그대로 남아 있어야 합니다.


def test_08_password_is_not_stored_as_md5(client, login):
    login("alice")
    with sqlite3.connect("board.db") as conn:
        stored = conn.execute("SELECT password_hash FROM users WHERE username = 'alice'").fetchone()[0]
    assert stored != hashlib.md5(b"club-pass-1234").hexdigest()
    assert stored.startswith("$argon2")


def test_09_weak_passwords_are_rejected(client):
    assert client.post("/signup", json={"username": "carol", "password": "1234"}).status_code == 422
    assert client.post("/signup", json={"username": "carol", "password": "carol-carol-1"}).status_code == 422


def test_10_login_is_locked_after_five_failures(client, login):
    login("alice")
    for _ in range(5):
        client.post("/login", json={"username": "alice", "password": "wrong-pass-0000"})
    res = client.post("/login", json={"username": "alice", "password": "club-pass-1234"})
    assert res.status_code == 429  # 맞는 비밀번호여도 잠긴 동안은 막습니다.


def test_11_secret_key_is_not_hardcoded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    sys.modules.pop("app", None)
    with pytest.raises(RuntimeError):
        importlib.import_module("app")  # 비밀 키가 없으면 실행을 멈춰야 합니다.
    sys.modules.pop("app", None)


def test_12_reset_code_is_not_predictable(client, login):
    login("alice")
    random.seed(2026)
    predicted = str(random.randint(100000, 999999))  # 공격자가 같은 시드로 미리 계산한 값
    random.seed(2026)
    client.post("/password-reset", params={"username": "alice"})
    with sqlite3.connect("board.db") as conn:
        stored = conn.execute("SELECT * FROM reset_codes").fetchone()[1]
    assert stored != predicted


def test_13_important_features_need_login(client, monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url, **kw: pytest.fail("로그인 없이 외부 요청을 보냈습니다."))
    body = "- title: 가짜 공지\n  body: 로그인 없이 넣은 공지\n"
    assert client.post("/notices/import", content=body).status_code in (401, 403)
    assert client.post("/files", files={"file": ("memo.txt", b"hello")}).status_code == 401
    assert client.get("/link-preview", params={"url": "https://example.com/"}).status_code == 401


# ---------- 시간 및 상태 ----------
def test_14_concurrent_likes_are_all_counted(client, notice):
    run_together(10, lambda i: client.post(f"/notices/{notice}/like"))
    assert client.get(f"/notices/{notice}").json()["likes"] == 10


def test_15_preview_retry_has_a_limit(board, client, login, monkeypatch):
    calls = []

    def always_fail(url, **kw):
        calls.append(url)
        if len(calls) > 20:
            raise RuntimeError("테스트를 멈추려고 일부러 낸 오류")  # 끝나지 않는 반복을 끊습니다.
        raise requests.ConnectionError("연결 실패")

    monkeypatch.setattr(requests, "get", always_fail)
    monkeypatch.setattr(board.time, "sleep", lambda seconds: None)
    headers = login("alice")
    client.get("/link-preview", params={"url": "https://example.com/"}, headers=headers)
    assert len(calls) <= 3


# ---------- 에러처리 ----------
def test_16_error_response_hides_details(board, client):
    @board.app.get("/boom")
    def boom():
        raise RuntimeError("db password is board-secret-0123")

    res = client.get("/boom")
    assert res.status_code == 500
    assert "board-secret" not in res.text and "Traceback" not in res.text


# ---------- 코드오류 ----------
def test_18_missing_notice_returns_404(client):
    assert client.get("/notices/9999").status_code == 404


# ---------- 캡슐화 ----------
def test_20_pickle_token_is_not_executed(client, tmp_path):
    token = base64.b64encode(pickle.dumps(MkdirOnLoad("pwned_by_token"))).decode()
    client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert not (tmp_path / "pwned_by_token").exists()


def test_20_forged_token_is_rejected(client):
    forged = {"id": 1, "username": "mallory", "role": "admin"}
    token = base64.b64encode(pickle.dumps(forged)).decode()
    res = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_21_signup_response_hides_password_hash(client):
    res = client.post("/signup", json={"username": "carol", "password": "club-pass-1234"})
    assert res.status_code == 201
    assert "password_hash" not in res.json()


def test_22_concurrent_me_requests_do_not_mix_users(client, login):
    headers = {"alice": login("alice"), "bob": login("bob")}
    names = ["alice", "bob"] * 4
    results = run_together(len(names), lambda i: client.get("/me", headers=headers[names[i]]).json())
    assert [r["username"] for r in results] == names  # 다른 사람의 정보가 섞이면 안 됩니다.


def test_23_debug_config_is_removed(client):
    assert client.get("/debug/config").status_code == 404


def test_23_login_does_not_print_password(client, login, capsys):
    login("alice")
    capsys.readouterr()
    client.post("/login", json={"username": "alice", "password": "club-pass-1234"})
    assert "club-pass-1234" not in capsys.readouterr().out


# ---------- API 오용 ----------
def test_24_yaml_import_does_not_run_code(client, admin_headers, tmp_path):
    body = "!!python/object/apply:os.mkdir ['pwned_by_yaml']\n"
    client.post("/notices/import", content=body, headers=admin_headers)
    assert not (tmp_path / "pwned_by_yaml").exists()
