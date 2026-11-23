"""개인정보와 비밀 값을 가리는 도구"""

def mask_email(email: str) -> str:
    """user1@example.com을 us***@example.com처럼 앞 두 글자와 도메인만 남깁니다."""
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    return f"{local[:2]}***@{domain}"
