import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import BEARER, CurrentUserDep, SessionDep
from app.errors import AppError
from app.models import RefreshToken, User
from app.schemas import RefreshRequest, Token, UserCreate, UserRead
from app.security import (DUMMY_HASH, create_access_token, create_refresh_token, hash_password,
                          hash_token, verify_password)
from app.services import login_guard

router = APIRouter(prefix="/auth", tags=["인증"])
logger = logging.getLogger(__name__)

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="회원가입",
             responses={409: {"description": "이미 가입된 이메일"}})
def signup(db: SessionDep, user_in: UserCreate):
    email = user_in.email.lower()  # 대문자로 적어도 같은 이메일로 봅니다.
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise AppError(409, "DUPLICATE_EMAIL", "이미 가입된 이메일입니다.")
    user = User(email=email, hashed_password=hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate(db: Session, email: str, password: str) -> User | None:
    """이메일과 비밀번호가 맞으면 사용자를, 틀리면 None을 돌려줍니다."""
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        verify_password(password, DUMMY_HASH)  # 없는 이메일도 비슷한 시간이 걸리게 합니다.
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def issue_tokens(db: Session, user: User) -> dict:
    """액세스 토큰과 리프레시 토큰을 함께 발급합니다. 리프레시 토큰은 해시만 저장합니다."""
    refresh_token = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))
    db.commit()
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": refresh_token,  # 원문은 이 응답에서 한 번만 내보냅니다.
        "token_type": "bearer",
    }

@router.post("/token", response_model=Token, summary="로그인(토큰 발급)",
             responses={401: {"description": "이메일 또는 비밀번호가 틀림"},
                        429: {"description": "로그인 시도가 너무 많음"}})
def login(request: Request, db: SessionDep, form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # OAuth2 규칙상 입력 칸 이름은 username입니다. 이 앱에서는 이메일을 넣습니다.
    email = form.username.lower()
    ip = request.client.host if request.client else "unknown"
    login_guard.check_allowed(db, email, ip)
    user = authenticate(db, email, form.password)
    if user is None:
        login_guard.record_failure(db, email, ip)
        logger.warning("로그인 실패")  # 입력한 이메일과 비밀번호는 로그에 남기지 않습니다.
        raise AppError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.", headers=BEARER)
    login_guard.reset(db, email)
    return issue_tokens(db, user)

@router.get("/me", response_model=UserRead, summary="내 정보 조회",
            responses={401: {"description": "로그인 필요"}})
def read_me(user: CurrentUserDep):
    return user

@router.post("/refresh", response_model=Token, summary="토큰 재발급",
             responses={401: {"description": "리프레시 토큰이 유효하지 않음"}})
def refresh(db: SessionDep, body: RefreshRequest):
    stored = db.scalar(select(RefreshToken).where(
        RefreshToken.token_hash == hash_token(body.refresh_token),
        RefreshToken.revoked.is_(False),
        RefreshToken.expires_at > datetime.now(timezone.utc),
    ))
    if stored is None:
        raise AppError(401, "INVALID_REFRESH_TOKEN", "리프레시 토큰이 유효하지 않거나 만료되었습니다.")
    stored.revoked = True  # 한 번 쓴 리프레시 토큰은 다시 쓰지 못하게 합니다.
    user = db.get(User, stored.user_id)
    return issue_tokens(db, user)  # 새 토큰 저장과 함께 위의 변경도 commit됩니다.

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="로그아웃")
def logout(db: SessionDep, body: RefreshRequest):
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(body.refresh_token)))
    if stored is not None:
        stored.revoked = True
        db.commit()
    # 없는 토큰이어도 204를 돌려줍니다. 로그아웃은 몇 번을 해도 결과가 같아야 합니다.
