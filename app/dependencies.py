from typing import Annotated

from fastapi import Depends, Query

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

def get_resource():
    """yield 의존성 연습용 함수입니다. 열고, 넘겨주고, 닫습니다."""
    print("자원을 엽니다.")
    try:
        yield "임시 자원"
    finally:
        print("자원을 닫습니다.")
