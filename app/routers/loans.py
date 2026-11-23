from fastapi import APIRouter, status

from app.dependencies import CurrentUserDep, SessionDep
from app.schemas import LoanCreate, LoanRead
from app.services import loans as loan_service

router = APIRouter(prefix="/loans", tags=["대여"])

@router.post("", response_model=LoanRead, status_code=status.HTTP_201_CREATED, summary="도서 대여",
             responses={401: {"description": "로그인 필요"}, 404: {"description": "도서를 찾을 수 없음"},
                        409: {"description": "이미 빌림, 대여 한도 초과, 재고 없음"}})
def borrow_book(db: SessionDep, user: CurrentUserDep, loan_in: LoanCreate):
    return loan_service.borrow(db, user, loan_in.book_id)

@router.get("/me", response_model=list[LoanRead], summary="내 대여 목록")
def list_my_loans(db: SessionDep, user: CurrentUserDep):
    return loan_service.my_loans(db, user)

@router.post("/{loan_id}/return", response_model=LoanRead, summary="도서 반납",
             responses={401: {"description": "로그인 필요"}, 403: {"description": "본인 대여가 아님"},
                        404: {"description": "대여 기록을 찾을 수 없음"}, 409: {"description": "이미 반납함"}})
def return_book(db: SessionDep, user: CurrentUserDep, loan_id: int):
    return loan_service.return_book(db, user, loan_id)
