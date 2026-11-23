"""표지 파일 저장소: 파일 검사와 저장, 삭제를 맡습니다. 데이터베이스는 다루지 않습니다."""
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.errors import AppError

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_COVER_SIZE = 2 * 1024 * 1024  # 2MB
COVER_DIR = Path(settings.upload_dir) / "covers"
COVER_URL_PREFIX = "/covers/"
LOG_FILE = Path("logs") / "upload.log"

def read_cover(file: UploadFile) -> tuple[bytes, str]:
    """확장자와 크기를 검사하고, 파일 내용과 확장자를 돌려줍니다."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(415, "UNSUPPORTED_FILE_TYPE", "jpg, jpeg, png 파일만 올릴 수 있습니다.")
    data = file.file.read(MAX_COVER_SIZE + 1)  # 한도보다 1바이트 더 읽어 보면 넘었는지 알 수 있습니다.
    if len(data) > MAX_COVER_SIZE:
        raise AppError(413, "FILE_TOO_LARGE", "파일 크기는 2MB를 넘을 수 없습니다.")
    if not data:
        raise AppError(422, "EMPTY_FILE", "빈 파일입니다.")
    return data, ext

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
    """업로드 기록을 파일에 한 줄씩 남깁니다."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    time.sleep(2)  # 실습용: 기록을 다른 서버로 보내는 데 2초 걸린다고 가정합니다.
    line = f"{datetime.now().isoformat(timespec='seconds')} book={book_id} user={user_id} file={original_name} size={size}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)
