from fastapi import APIRouter, Depends

from app.dependencies import PageDep, SessionDep, require_admin
from app.errors import AppError
from app.models import User
from app.repositories import loans as loan_repo
from app.repositories import users as user_repo
from app.schemas import LoanRead, UserRead, UserSummary

# 이 라우터의 모든 API에 관리자 검사를 한 번에 겁니다.
router = APIRouter(prefix="/admin", tags=["관리자"], dependencies=[Depends(require_admin)])

@router.get("/users", response_model=list[UserSummary], summary="전체 사용자 목록(이메일 일부 가림)")
def list_users(db: SessionDep, page: PageDep):
    return user_repo.list_users(db, page.skip, page.limit)

@router.get("/users/{user_id}", response_model=UserRead, summary="사용자 상세 조회",
            responses={404: {"description": "사용자를 찾을 수 없음"}})
def get_user(db: SessionDep, user_id: int):
    user = db.get(User, user_id)
    if user is None:
        raise AppError(404, "USER_NOT_FOUND", f"{user_id}번 사용자를 찾을 수 없습니다.")
    return user

@router.get("/loans", response_model=list[LoanRead], summary="전체 대여 목록")
def list_loans(db: SessionDep, page: PageDep):
    return loan_repo.list_all(db, page.skip, page.limit)
