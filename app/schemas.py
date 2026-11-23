from pydantic import BaseModel, ConfigDict, Field

class BookCreate(BaseModel):
    """등록과 전체 수정(PUT)에 쓰는 입력 모델"""
    title: str = Field(min_length=1, max_length=100, examples=["FastAPI 실전"])
    author: str = Field(min_length=1, max_length=50, examples=["최유나"])
    price: int = Field(ge=0, le=1_000_000, examples=[27000])
    isbn: str | None = Field(default=None, pattern=r"^\d{13}$", examples=["9791100000035"])

class BookUpdate(BaseModel):
    """일부 수정(PATCH)에 쓰는 입력 모델. 모든 항목이 선택입니다."""
    title: str | None = Field(default=None, min_length=1, max_length=100)
    author: str | None = Field(default=None, min_length=1, max_length=50)
    price: int | None = Field(default=None, ge=0, le=1_000_000)
    isbn: str | None = Field(default=None, pattern=r"^\d{13}$")

class BookRead(BaseModel):
    """응답에 쓰는 출력 모델. 여기에 없는 필드는 응답에서 빠집니다."""

    # ORM 객체의 속성(book.title)에서도 값을 읽을 수 있게 합니다.
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    price: int
    isbn: str | None = None

class BookPage(BaseModel):
    """목록 응답. 현재 페이지의 도서와 전체 개수를 함께 돌려줍니다."""
    items: list[BookRead]
    total: int
    skip: int
    limit: int
