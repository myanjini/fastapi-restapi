from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import SessionDep
from app.errors import AppError
from app.models import User
from app.schemas import Token, UserCreate, UserRead
from app.security import DUMMY_HASH, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["인증"])

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

# 401 응답에는 어떤 방식으로 인증해야 하는지 알려 주는 헤더를 붙입니다.
BEARER = {"WWW-Authenticate": "Bearer"}

def authenticate(db: Session, email: str, password: str) -> User | None:
    """이메일과 비밀번호가 맞으면 사용자를, 틀리면 None을 돌려줍니다."""
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        verify_password(password, DUMMY_HASH)  # 없는 이메일도 비슷한 시간이 걸리게 합니다.
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/token", response_model=Token, summary="로그인(토큰 발급)",
             responses={401: {"description": "이메일 또는 비밀번호가 틀림"}})
def login(db: SessionDep, form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # OAuth2 규칙상 입력 칸 이름은 username입니다. 이 앱에서는 이메일을 넣습니다.
    user = authenticate(db, form.username, form.password)
    if user is None:
        raise AppError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.", headers=BEARER)
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}
