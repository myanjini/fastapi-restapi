"""로그인 시도 제한: 계정과 IP마다 일정 시간 안의 실패 횟수를 셉니다."""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.errors import AppError
from app.repositories import login_failures as failure_repo

WINDOW = timedelta(minutes=15)   # 이 시간 안의 실패만 셉니다.
MAX_FAILURES_PER_EMAIL = 5       # 한 계정에 대한 실패 허용 횟수
MAX_FAILURES_PER_IP = 20         # 한 IP에서의 실패 허용 횟수(여러 계정을 돌아가며 시도하는 공격 대비)

def check_allowed(db: Session, email: str, ip: str) -> None:
    """실패가 너무 많으면 비밀번호를 확인하기 전에 429로 막습니다."""
    since = datetime.now(timezone.utc) - WINDOW
    if (failure_repo.count_since(db, since, email=email) >= MAX_FAILURES_PER_EMAIL
            or failure_repo.count_since(db, since, ip=ip) >= MAX_FAILURES_PER_IP):
        raise AppError(429, "TOO_MANY_ATTEMPTS", "로그인 시도가 너무 많습니다. 15분 뒤에 다시 시도하세요.",
                       headers={"Retry-After": str(int(WINDOW.total_seconds()))})

def record_failure(db: Session, email: str, ip: str) -> None:
    failure_repo.add(db, email, ip, datetime.now(timezone.utc))
    db.commit()

def reset(db: Session, email: str) -> None:
    """로그인에 성공하면 그 계정의 실패 기록을 지웁니다. 확정은 토큰 발급과 함께 합니다."""
    failure_repo.clear(db, email)
