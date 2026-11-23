# FastAPI로 배우는 REST API 백엔드 개발: 예제 저장소

「FastAPI로 배우는 REST API 백엔드 개발」의 실습 코드입니다. 책에서 만드는 도서 관리 API의 코드가 절 단위의 브랜치로 나뉘어 있습니다.
예를 들어 `p2-done` 브랜치에는 1.6절의 실습을 마친 코드가 들어 있습니다.

이 main 브랜치에는 안내 문서와 양식만 있습니다. 실습 코드는 아래 표의 브랜치에서 봅니다.

## 브랜치 목록

| 브랜치 | 장 | 절 | 내용 |
|---|---|---|---|
| `p2-done` | 1장 | 1.6 | 첫 FastAPI 앱 |
| `p3-done` | 1장 | 1.8 | 도서 조회 API |
| `p4-done` | 1장 | 1.11 | 도서 등록 API |
| `p5-done` | 2장 | 2.3 | 응답 모델과 수정, 삭제 API |
| `p6-done` | 2장 | 2.7 | 오류 응답 통일과 API 문서 |
| `p7-done` | 2장 | 2.9 | APIRouter로 구조화 |
| `p8-done` | 3장 | 3.2 | 의존성 활용하기 |
| `p9-done` | 3장 | 3.6 | 설정 분리와 CORS, 요청 로깅 |
| `p11-done` | 3장 | 3.10 | 데이터베이스 연동 |
| `p12-done` | 4장 | 4.4 | 수정, 삭제와 목록 조회 고도화 |
| `p13-done` | 4장 | 4.6 | 저자 API와 관계 조회 |
| `p14-done` | 4장 | 4.8 | Alembic 마이그레이션 |
| `p15-done` | 5장 | 5.2 | 회원가입 API |
| `p16-done` | 5장 | 5.4 | 로그인 API |
| `p17-done` | 5장 | 5.6 | 소유자와 관리자 권한 |
| `p18-done` | 5장 | 5.9 | 리프레시 토큰과 로그아웃 |
| `p19-done` | 6장 | 6.3 | 서비스 계층 적용 |
| `p20-done` | 6장 | 6.6 | 표지 이미지 업로드 |
| `p21-done` | 6장 | 6.7-6.8 | 백그라운드 작업과 도서 대여 |
| `p22-done` | 7장 | 7.3 | CRUD 테스트 작성 |
| `p23-done` | 7장 | 7.5 | fixture와 테스트 격리 |
| `p24-done` | 7장 | 7.7-7.9 | 인증, 대여, 업로드 테스트와 커버리지 |
| `p25-done` | 7장 | 7.11 | GitHub Actions CI |
| `p26-done` | 8장 | 8.3 | Dockerfile |
| `p27-done` | 8장 | 8.6 | Docker Compose와 PostgreSQL |
| `p28-done` | 8장 | 8.10-8.11 | 로깅과 헬스 체크 |
| `p30-done` | 9장 | 9.6-9.7 | SQL 삽입, 경로 조작 조치 |
| `p31-done` | 9장 | 9.10 | 업로드 API 보안 강화 |
| `p32-done` | 9장 | 9.13-9.14 | 권한 검사 보강과 입력 필드 최소화 |
| `p33-done` | 10장 | 10.3 | 비밀정보 정리와 이메일 가리기 |
| `p34-done` | 10장 | 10.7 | 로그인 시도 제한과 비밀번호 규칙 |
| `p35-done` | 10장 | 10.11 | 안전한 오류 응답 |
| `p36-done` | 11장 | 11.3 | 경쟁 조건 해결 |
| `p37-done` | 11장 | 11.7 | CI에 보안 점검 추가 |
| `p47-done` | 14장 | 14.3 | Parameter Store에서 비밀 값 읽기 |
| `p49-done` | 14장 | 14.9 | 운영용 Compose 파일 |
| `p50-done` | 15장 | 15.3 | 표지 이미지를 S3에 저장 |
| `p51-done` | 15장 | 15.6 | CloudWatch 로그 드라이버와 ALB 설정 |
| `p53-done` | 15장 | 15.14 | GitHub Actions 배포 자동화 |
| `p54-done` | 16장 | 16.3 | 운영 CORS 설정 |
| `security-lab` | 9장, 11장 | 9.6, 11.8~11.14 | 보안약점 진단 실습 자료(게시판 API), 9장의 위험한 코드 |

12장과 13장은 AWS 콘솔과 서버에서 하는 실습이라 코드가 바뀌지 않습니다. 13장까지의 코드는 `p37-done`과 같습니다.
17장과 18장의 미니 프로젝트는 각자 주제를 정해 새 저장소에서 진행하므로 이 저장소에 브랜치가 없습니다.

## 사용 방법

저장소를 내려받고 원하는 브랜치로 바꿉니다. 내가 실습하는 C:\book-api 폴더와 섞이지 않도록 다른 폴더(C:\fastapi-restapi)에 내려받습니다.

```
C:\> git clone https://github.com/myanjini/fastapi-restapi.git
C:\> cd fastapi-restapi
C:\fastapi-restapi> git branch -r
C:\fastapi-restapi> git switch p14-done
```

브랜치를 바꾼 뒤에는 그 브랜치의 패키지를 설치합니다. 3.10절(p11-done)부터 requirements.txt가 있습니다. `.env`는 저장소에 없으므로 3.6절(p9-done)부터는 `.env.example`을 복사해 만들고 SECRET_KEY를 채웁니다.

```
C:\fastapi-restapi> python -m venv .venv
C:\fastapi-restapi> .venv\Scripts\activate
(.venv) C:\fastapi-restapi> pip install -r requirements.txt
(.venv) C:\fastapi-restapi> copy .env.example .env
(.venv) C:\fastapi-restapi> python -c "import secrets; print(secrets.token_urlsafe(32))"
```

4장(p14-done)부터는 서버를 실행하기 전에 `alembic upgrade head`로 테이블을 만듭니다. 7장(p23-done)부터는 `pytest`로 테스트를 실행할 수 있습니다.

내 코드와 완성 코드를 비교하거나, 한 절에서 무엇이 바뀌었는지 보려면 `git diff`를 씁니다.

```
(.venv) C:\fastapi-restapi> git diff p13-done p14-done --stat
(.venv) C:\fastapi-restapi> git diff p13-done p14-done -- app/models.py
C:\> code --diff C:\book-api\app\models.py C:\fastapi-restapi\app\models.py
```

## 이 main 브랜치에 들어 있는 것

| 위치 | 내용 |
|---|---|
| docs/templates/ | 부록 B(API 명세서), C(배포 전 보안 점검), D(발표 체크리스트), F(보안약점 진단, 조치 결과표), G(AWS 자원 정리) 양식 |
| downloads/security-lab.zip | 11장 보안약점 진단 실습 자료. `security-lab` 브랜치와 같은 내용입니다. |

## 주의

- `security-lab` 브랜치와 security-lab.zip에는 일부러 넣은 보안약점이 있습니다. 내 컴퓨터의 127.0.0.1에서만 실행하고 인터넷에 공개하지 않습니다.
- 14장 이후의 운영 설정(compose.prod.yaml, .github/workflows/deploy.yml)은 책의 예시 값(계정 ID, 버킷 이름 등)을 씁니다. 내 AWS 자원에 맞게 바꿔 씁니다.
- 실습 데이터는 모두 가상 데이터입니다(부록 E).
