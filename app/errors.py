class AppError(Exception):
    """이 앱이 일부러 보내는 오류. 상태 코드, 오류 코드, 메시지를 담습니다."""

    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
