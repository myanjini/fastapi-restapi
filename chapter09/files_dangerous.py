# 9.7절: 경로 조작이 가능한 위험한 코드입니다. 도서 API의 app/routers/files.py에 잠시 넣어 공격을 재현할 때만 씁니다.
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.errors import AppError

router = APIRouter(prefix="/files", tags=["자료실"])

FILES_DIR = Path("files")  # 이용 안내 같은 공개 자료를 두는 폴더

@router.get("/download", summary="자료 내려받기")
def download_file(name: str):
    # 위험한 코드: 사용자가 보낸 이름을 그대로 경로에 붙였습니다.
    path = FILES_DIR / name
    if not path.is_file():
        raise AppError(404, "FILE_NOT_FOUND", "파일을 찾을 수 없습니다.")
    return FileResponse(path)
