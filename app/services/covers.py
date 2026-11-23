"""표지 파일 저장소: 파일 검사와 저장, 삭제를 맡습니다. 데이터베이스는 다루지 않습니다."""
import logging
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.errors import AppError

# 허용하는 확장자와, 그 확장자일 때 내용이 되어야 하는 형식
ALLOWED_EXTENSIONS = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png"}
MAX_COVER_SIZE = 2 * 1024 * 1024  # 2MB
COVER_DIR = Path(settings.upload_dir) / "covers"
COVER_URL_PREFIX = "/covers/"
logger = logging.getLogger(__name__)

# 파일 앞부분에 들어 있는 형식 표시(매직 넘버)와, 그 형식으로 저장할 확장자
SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpg",
}

def detect_image_type(data: bytes) -> str | None:
    """파일 내용의 앞부분을 보고 png인지 jpg인지 판단합니다."""
    for signature, ext in SIGNATURES.items():
        if data.startswith(signature):
            return ext
    return None

def read_cover(file: UploadFile) -> tuple[bytes, str]:
    """확장자, 크기, 내용을 검사하고, 파일 내용과 저장할 확장자를 돌려줍니다."""
    expected = ALLOWED_EXTENSIONS.get(Path(file.filename or "").suffix.lower())
    if expected is None:
        raise AppError(415, "UNSUPPORTED_FILE_TYPE", "jpg, jpeg, png 파일만 올릴 수 있습니다.")
    data = file.file.read(MAX_COVER_SIZE + 1)  # 한도보다 1바이트 더 읽어 보면 넘었는지 알 수 있습니다.
    if len(data) > MAX_COVER_SIZE:
        raise AppError(413, "FILE_TOO_LARGE", "파일 크기는 2MB를 넘을 수 없습니다.")
    if not data:
        raise AppError(422, "EMPTY_FILE", "빈 파일입니다.")
    if detect_image_type(data) != expected:
        raise AppError(415, "INVALID_IMAGE_CONTENT", "파일 내용이 확장자에 맞는 이미지가 아닙니다.")
    return data, expected  # 저장할 때는 확인한 형식의 확장자를 씁니다.

def clean_filename(name: str | None) -> str:
    """기록에 남길 원래 파일 이름에서 경로와 제어 문자를 없애고 길이를 줄입니다."""
    name = (name or "").replace("\\", "/").rsplit("/", 1)[-1]  # 폴더 부분을 떼어 냅니다.
    name = "".join(ch for ch in name if ch.isprintable())   # 줄바꿈 같은 보이지 않는 문자를 지웁니다.
    return name[:100] or "unnamed"

def save_cover(data: bytes, ext: str) -> str:
    """겹치지 않는 새 이름으로 저장하고, 브라우저에서 열 주소를 돌려줍니다."""
    filename = f"{uuid.uuid4().hex}{ext}"
    (COVER_DIR / filename).write_bytes(data)
    return COVER_URL_PREFIX + filename

def remove_cover(cover_url: str | None) -> None:
    """저장해 둔 표지 파일을 지웁니다. 없으면 아무것도 하지 않습니다."""
    if cover_url:
        (COVER_DIR / Path(cover_url).name).unlink(missing_ok=True)

def write_upload_log(book_id: int, user_id: int, original_name: str, size: int) -> None:
    """업로드 기록을 로그로 남깁니다."""
    logger.info("표지 업로드", extra={"book_id": book_id, "user_id": user_id,
                                      "original_name": original_name, "size": size})
