"""로그 설정: 모든 로그를 한 줄짜리 JSON으로 표준 출력에 씁니다."""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

from app.privacy import mask_text

# 지금 처리 중인 요청의 ID. 요청마다 따로 보관됩니다.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

# LogRecord가 원래 가진 속성 이름. 이 밖의 속성은 extra로 넘긴 값입니다.
_STANDARD_KEYS = set(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {"message", "taskName", "color_message"}

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "time": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_text(record.getMessage()),
            "request_id": request_id_var.get(),
        }
        for key, value in record.__dict__.items():  # extra로 넘긴 값을 덧붙입니다.
            if key not in _STANDARD_KEYS:
                data[key] = mask_text(value) if isinstance(value, str) else value
        if record.exc_info:
            data["error"] = mask_text(self.formatException(record.exc_info))
        return json.dumps(data, ensure_ascii=False, default=str)

def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
    # uvicorn의 로그도 같은 형식으로 내보내고, 요청 기록은 우리 미들웨어가 남기므로 끕니다.
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    logging.getLogger("uvicorn.access").disabled = True
