from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError
from app.models import User
from app.security import decode_access_token

class Pagination:
    """목록 API가 함께 쓰는 페이지 나누기 값입니다."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="건너뛸 개수"),
        limit: int = Query(default=10, ge=1, le=100, description="가져올 최대 개수"),
    ):
        self.skip = skip
        self.limit = limit

# 타입과 의존성을 한 이름으로 묶어 두면 여러 함수에서 짧게 쓸 수 있습니다.
PageDep = Annotated[Pagination, Depends()]
SessionDep = Annotated[Session, Depends(get_db)]

# 요청의 Authorization 헤더에서 "Bearer 토큰"의 토큰 부분을 꺼내 줍니다.
# tokenUrl은 Swagger UI의 Authorize 창이 로그인할 때 부를 주소입니다.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)
TokenDep = Annotated[str | None, Depends(oauth2_scheme)]

BEARER = {"WWW-Authenticate": "Bearer"}

def get_current_user(db: SessionDep, token: TokenDep) -> User:
    """토큰을 검사해 지금 요청을 보낸 사용자를 돌려줍니다."""
    if token is None:
        raise AppError(401, "NOT_AUTHENTICATED", "로그인이 필요합니다.", headers=BEARER)
    user_id = decode_access_token(token)
    if user_id is None:
        raise AppError(401, "INVALID_TOKEN", "토큰이 유효하지 않거나 만료되었습니다.", headers=BEARER)
    user = db.get(User, user_id)
    if user is None:  # 토큰은 올바르지만 그사이 탈퇴한 사용자
        raise AppError(401, "INVALID_TOKEN", "토큰이 유효하지 않거나 만료되었습니다.", headers=BEARER)
    return user

CurrentUserDep = Annotated[User, Depends(get_current_user)]

def require_admin(user: CurrentUserDep) -> User:
    """관리자가 아니면 403으로 막습니다."""
    if user.role != "admin":
        raise AppError(403, "FORBIDDEN", "관리자만 사용할 수 있습니다.")
    return user
