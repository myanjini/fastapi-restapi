"""보고서 저장소: 집계와 보고서는 SQL로 직접 작성합니다."""
from sqlalchemy import text
from sqlalchemy.orm import Session

# 정렬 기준은 값 바인딩을 쓸 수 없으므로 허용 목록에서 꺼낸 글자만 SQL에 넣습니다.
ORDER_COLUMNS = {"title": "title", "stock": "stock"}

def stock_report(db: Session, keyword: str, order_by: str) -> list[dict]:
    sql = text(f"""
        SELECT b.title, a.name AS author, b.stock
        FROM books b JOIN authors a ON a.id = b.author_id
        WHERE b.title LIKE :pattern
        ORDER BY {ORDER_COLUMNS[order_by]}, b.id
    """)
    # :pattern 자리에는 값이 따로 전달되므로 SQL 문장의 구조를 바꿀 수 없습니다.
    rows = db.execute(sql, {"pattern": f"%{keyword}%"}).mappings()
    return [dict(row) for row in rows]
