from app.security import hash_password, verify_password

def test_hash_is_not_plain_password():
    # 준비
    password = "practice-pass-1"
    # 실행
    hashed = hash_password(password)
    # 검증
    assert hashed != password
    assert hashed.startswith("$argon2id$")

def test_verify_password():
    hashed = hash_password("practice-pass-1")
    assert verify_password("practice-pass-1", hashed) is True
    assert verify_password("wrong-pass", hashed) is False
