from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import settings

# 지금 권장되는 알고리즘(Argon2)으로 비밀번호 해시를 만드는 도구입니다.
password_hash = PasswordHash.recommended()

# 없는 이메일로 로그인할 때 비교용으로 쓰는 가짜 해시입니다.
DUMMY_HASH = password_hash.hash("dummy-password")

def hash_password(password: str) -> str:
    """비밀번호를 해시로 바꿉니다. 같은 비밀번호도 호출할 때마다 다른 결과가 나옵니다."""
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """입력한 비밀번호가 저장된 해시와 맞는지 확인합니다."""
    return password_hash.verify(password, hashed)

ALGORITHM = "HS256"  # 비밀 키 하나로 서명하고 검증하는 방식

def create_access_token(user_id: int) -> str:
    """사용자 번호와 만료 시각을 담아 서명한 JWT를 만듭니다."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def decode_access_token(token: str) -> int | None:
    """토큰이 올바르면 사용자 번호를, 아니면 None을 돌려줍니다."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],              # 이 방식으로 서명한 토큰만 받습니다.
            options={"require": ["exp", "sub"]},  # 만료 시각과 사용자 번호가 꼭 있어야 합니다.
        )
    except jwt.InvalidTokenError:  # 서명이 틀렸거나, 만료되었거나, 형식이 깨진 경우
        return None
    return int(payload["sub"])
