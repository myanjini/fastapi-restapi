from typing import Literal

from fastapi import APIRouter, Query

from app.dependencies import CurrentUserDep, SessionDep
from app.repositories import reports as report_repo
from app.schemas import StockReportRow

router = APIRouter(prefix="/reports", tags=["보고서"])

@router.get("/stock", response_model=list[StockReportRow], summary="재고 현황 보고서")
def stock_report(
    db: SessionDep,
    user: CurrentUserDep,
    keyword: str = Query(default="", max_length=100, description="제목에 들어간 글자"),
    order_by: Literal["title", "stock"] = Query(default="stock", description="정렬 기준"),
):
    return report_repo.stock_report(db, keyword, order_by)
