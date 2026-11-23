"""개인정보와 비밀 값을 가리는 도구"""
import re

def mask_email(email: str) -> str:
    """user1@example.com을 us***@example.com처럼 앞 두 글자와 도메인만 남깁니다."""
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    return f"{local[:2]}***@{domain}"

# 로그에 섞여 들어오면 가릴 값들
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
JWT_PATTERN = re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]+")
PASSWORD_HASH_PATTERN = re.compile(r"\$argon2[a-z]*\$[^\s'\",)]+")

def mask_text(text: str) -> str:
    """글자 속의 이메일, 토큰, 비밀번호 해시를 가립니다."""
    text = JWT_PATTERN.sub("[TOKEN]", text)
    text = PASSWORD_HASH_PATTERN.sub("[PASSWORD_HASH]", text)
    return EMAIL_PATTERN.sub(lambda m: mask_email(m.group()), text)
