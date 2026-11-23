# 1. 베이스 이미지: Python 3.12가 설치된 가벼운 리눅스
FROM python:3.12-slim

# 2. Python 실행 설정: .pyc 파일을 만들지 않고, 출력을 모아 두지 않고 바로 내보냅니다.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. 컨테이너 안의 작업 폴더
WORKDIR /app

# 4. 패키지 목록만 먼저 복사해 설치합니다. 코드만 바뀌면 이 단계는 캐시를 씁니다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 소스 코드 복사(.dockerignore에 적은 것은 빠집니다)
COPY . .

# 6. 관리자(root)가 아닌 사용자를 만들고, 이 사용자가 쓸 폴더만 쓰기 권한을 줍니다.
RUN useradd --create-home appuser \
    && mkdir -p uploads logs data \
    && chown appuser uploads logs data
USER appuser

# 7. 컨테이너가 시작할 때 실행할 명령
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
