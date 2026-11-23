# 9.5절: SQL 삽입이 가능한 위험한 코드입니다. 도서 API의 app/repositories/reports.py에 잠시 넣어 공격을 재현할 때만 씁니다.
"""보고서 저장소: 집계와 보고서는 SQL로 직접 작성합니다."""
from sqlalchemy import text
from sqlalchemy.orm import Session

def stock_report(db: Session, keyword: str, order_by: str) -> list[dict]:
    # 위험한 코드: 사용자가 보낸 값을 SQL 문장에 그대로 이어 붙였습니다.
    sql = f"""
        SELECT b.title, a.name AS author, b.stock
        FROM books b JOIN authors a ON a.id = b.author_id
        WHERE b.title LIKE '%{keyword}%'
        ORDER BY {order_by}
    """
    return [dict(row) for row in db.execute(text(sql)).mappings()]
