from fastapi import APIRouter, status
from sqlalchemy import select

from app.dependencies import SessionDep
from app.errors import AppError
from app.models import User
from app.schemas import UserCreate, UserRead
from app.security import hash_password

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
