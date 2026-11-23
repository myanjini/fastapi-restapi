from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    """회원가입에 쓰는 입력 모델"""
    email: EmailStr = Field(examples=["user1@example.com"])
    password: str = Field(min_length=8, max_length=64, examples=["practice-pass-1"])

class UserRead(BaseModel):
    """사용자 응답 모델. 비밀번호 해시는 넣지 않습니다."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str

class Token(BaseModel):
    """로그인과 재발급 응답. 두 토큰을 함께 돌려줍니다."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    """재발급과 로그아웃 요청 본문"""
    refresh_token: str = Field(min_length=1)

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
    stock: int = Field(default=0, ge=0, le=1000, examples=[3])  # 처음 들여오는 수량

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
    stock: int
    cover_url: str | None = None
    author: AuthorRead
    owner_id: int | None = None

class StockChange(BaseModel):
    """재고 변경 요청 본문"""
    change: int = Field(ge=-1000, le=1000, examples=[5])  # 늘릴 때 양수, 줄일 때 음수
    reason: str = Field(min_length=1, max_length=20, examples=["입고"])

class BookPage(BaseModel):
    """목록 응답. 현재 페이지의 도서와 전체 개수를 함께 돌려줍니다."""
    items: list[BookRead]
    total: int
    skip: int
    limit: int

class LoanCreate(BaseModel):
    """대여 요청 본문"""
    book_id: int = Field(gt=0, examples=[1])

class BookBrief(BaseModel):
    """대여 응답에 넣는 도서 요약"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str

class LoanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book: BookBrief
    loaned_at: datetime
    returned_at: datetime | None = None
