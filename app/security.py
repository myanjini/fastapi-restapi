from pwdlib import PasswordHash

# 지금 권장되는 알고리즘(Argon2)으로 비밀번호 해시를 만드는 도구입니다.
password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    """비밀번호를 해시로 바꿉니다. 같은 비밀번호도 호출할 때마다 다른 결과가 나옵니다."""
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """입력한 비밀번호가 저장된 해시와 맞는지 확인합니다."""
    return password_hash.verify(password, hashed)
