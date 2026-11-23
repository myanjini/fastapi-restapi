from fastapi import APIRouter, Depends

from app.dependencies import PageDep, SessionDep, require_admin
from app.repositories import loans as loan_repo
from app.repositories import users as user_repo
from app.schemas import LoanRead, UserRead

# 이 라우터의 모든 API에 관리자 검사를 한 번에 겁니다.
router = APIRouter(prefix="/admin", tags=["관리자"], dependencies=[Depends(require_admin)])

@router.get("/users", response_model=list[UserRead], summary="전체 사용자 목록")
def list_users(db: SessionDep, page: PageDep):
    return user_repo.list_users(db, page.skip, page.limit)

@router.get("/loans", response_model=list[LoanRead], summary="전체 대여 목록")
def list_loans(db: SessionDep, page: PageDep):
    return loan_repo.list_all(db, page.skip, page.limit)
