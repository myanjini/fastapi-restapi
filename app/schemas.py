from pydantic import BaseModel, ConfigDict, Field

class AuthorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50, examples=["김하늘"])

class AuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class BookCreate(BaseModel):
    """등록에 쓰는 입력 모델"""
    title: str = Field(min_length=1, max_length=100, examples=["FastAPI 실전"])
    author_id: int = Field(gt=0, examples=[1])
    price: int = Field(ge=0, le=1_000_000, examples=[27000])
    isbn: str | None = Field(default=None, pattern=r"^\d{13}$", examples=["9791100000035"])
    published_year: int | None = Field(default=None, ge=1900, le=2100)

class BookUpdate(BaseModel):
    """일부 수정(PATCH)에 쓰는 입력 모델. 모든 항목이 선택입니다."""
    title: str | None = Field(default=None, min_length=1, max_length=100)
    author_id: int | None = Field(default=None, gt=0)
    price: int | None = Field(default=None, ge=0, le=1_000_000)
    isbn: str | None = Field(default=None, pattern=r"^\d{13}$")
    published_year: int | None = Field(default=None, ge=1900, le=2100)

class BookRead(BaseModel):
    """응답에 쓰는 출력 모델. 저자는 이름까지 담아 중첩해서 보냅니다."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: int
    isbn: str | None = None
    published_year: int | None = None
    author: AuthorRead

class BookPage(BaseModel):
    """목록 응답. 현재 페이지의 도서와 전체 개수를 함께 돌려줍니다."""
    items: list[BookRead]
    total: int
    skip: int
    limit: int
