from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.errors import AppError

router = APIRouter(prefix="/files", tags=["자료실"])

FILES_DIR = Path("files").resolve()  # 이용 안내 같은 공개 자료를 두는 폴더(절대 경로)

def safe_path(name: str) -> Path:
    """자료실 폴더 안의 파일만 가리키는지 확인한 실제 경로를 돌려줍니다."""
    path = (FILES_DIR / name).resolve()  # ..와 바로 가기를 모두 풀어 실제 경로로 바꿉니다.
    if not path.is_relative_to(FILES_DIR):
        raise AppError(400, "INVALID_FILE_NAME", "허용되지 않는 파일 이름입니다.")
    return path

@router.get("/download", summary="자료 내려받기")
def download_file(
    name: str = Query(max_length=100, pattern=r"^[\w.\-]+$", description="파일 이름(글자, 숫자, 점, 하이픈만)"),
):
    path = safe_path(name)
    if not path.is_file():
        raise AppError(404, "FILE_NOT_FOUND", "파일을 찾을 수 없습니다.")
    # filename을 주면 브라우저가 화면에 열지 않고 내려받기로 처리합니다.
    return FileResponse(path, filename=path.name)
