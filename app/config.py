from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """환경 변수와 .env 파일에서 설정값을 읽습니다. 이름은 대소문자를 가리지 않습니다."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "도서 관리 API"
    database_url: str = "sqlite:///./books.db"
    secret_key: str  # 기본값이 없으므로 반드시 설정해야 합니다.
    access_token_expire_minutes: int = 15  # 액세스 토큰 유효 시간(분). 재발급이 생겨 짧게 줄입니다.
    refresh_token_expire_days: int = 14  # 리프레시 토큰 유효 기간(일)
    cors_origins: list[str] = ["http://localhost:5173"]

settings = Settings()
