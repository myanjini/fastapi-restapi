from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 예시나 기본값으로 흔히 쓰이는, 비밀 키로 쓰면 안 되는 값
WEAK_SECRETS = {"change-me", "changeme", "secret", "secret-key", "your-secret-key"}

class Settings(BaseSettings):
    """환경 변수와 .env 파일에서 설정값을 읽습니다. 이름은 대소문자를 가리지 않습니다."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # .env에 Compose가 쓰는 값(POSTGRES_PASSWORD)이 있어도 오류 없이 넘어갑니다.
        hide_input_in_errors=True,  # 설정 오류 메시지에 입력한 값(비밀 키)을 찍지 않습니다.
    )

    app_name: str = "도서 관리 API"
    database_url: str = "sqlite:///./books.db"
    secret_key: str  # 기본값이 없으므로 반드시 설정해야 합니다.
    access_token_expire_minutes: int = 15  # 액세스 토큰 유효 시간(분)
    refresh_token_expire_days: int = 14  # 리프레시 토큰 유효 기간(일)
    upload_dir: str = "uploads"  # 올린 파일을 저장할 폴더
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR 중 하나
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("secret_key")
    @classmethod
    def check_secret_key(cls, value: str) -> str:
        """예시 값이나 짧은 값으로는 서버가 시작하지 않게 합니다."""
        if len(value) < 32 or value.lower() in WEAK_SECRETS:
            raise ValueError("SECRET_KEY는 secrets 모듈로 만든 32자 이상의 값이어야 합니다.")
        return value

settings = Settings()
