# 9.12절: 소유자 검사가 빠진 위험한 코드입니다. 도서 API의 app/routers/loans.py와 app/services/loans.py에 잠시 넣어 공격을 재현할 때만 씁니다.

# app/routers/loans.py의 GET /me 아래
@router.get("/{loan_id}", response_model=LoanRead, summary="대여 상세 조회",
            responses={401: {"description": "로그인 필요"}, 404: {"description": "대여 기록을 찾을 수 없음"}})
def get_loan(db: SessionDep, user: CurrentUserDep, loan_id: int):
    return loan_service.get_loan(db, user, loan_id)


# app/services/loans.py
def get_loan(db: Session, user: User, loan_id: int) -> Loan:
    loan = loan_repo.get(db, loan_id)
    if loan is None:
        raise AppError(404, "LOAN_NOT_FOUND", f"{loan_id}번 대여 기록을 찾을 수 없습니다.")
    return loan  # 위험한 코드: 로그인만 확인하고, 누구의 대여인지는 확인하지 않았습니다.
