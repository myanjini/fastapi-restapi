# security-lab: 보안약점 진단 실습 자료

「FastAPI로 배우는 REST API 백엔드 개발」 11장의 보안약점 진단 실습(11.8절~11.14절)에서 쓰는 자료입니다.
진단 대상은 보안약점이 일부러 섞여 있는 "동아리 공지 게시판" API입니다.

> 주의: 이 코드에는 실제로 공격할 수 있는 약점이 들어 있습니다. 내 컴퓨터의 127.0.0.1에서만 실행하고,
> 클라우드 서버에 올리거나 다른 사람이 접속할 수 있게 열지 않습니다.

## 들어 있는 파일

| 파일 | 내용 |
|---|---|
| app.py | 진단할 게시판 API입니다. 한 파일이며 FastAPI와 Python 내장 sqlite3 모듈로 만들었습니다. |
| diagnosis.md | 진단표 양식(부록 F와 같은 형식)입니다. 여기에 결과를 적습니다. |
| tests/ | 보안 테스트입니다. 11.12절에서 씁니다. 진단을 마치기 전에는 열어 보지 않습니다. 테스트 이름이 정답의 힌트가 됩니다. |
| chapter09/ | 9장에서 공격을 재현할 때 쓴 도서 API의 위험한 코드입니다. 도서 API의 각 브랜치에는 고친 코드만 있습니다. |
| solution/ | 11.14절의 모범 조치 코드와 조치 후의 requirements.txt입니다. 직접 조치를 마친 뒤에 비교합니다. |

## 준비

도서 API와 다른 폴더(예: C:\security-lab)에서 작업합니다. 명령 프롬프트에서 실행합니다.

```
C:\security-lab> python -m venv .venv
C:\security-lab> .venv\Scripts\activate
(.venv) C:\security-lab> pip install -r requirements.txt
```

## 서버 띄우기(11.9절)

```
(.venv) C:\security-lab> uvicorn app:app --reload
```

브라우저에서 http://127.0.0.1:8000/docs 를 열어 요청을 보내 봅니다. 실행하면 같은 폴더에 board.db와 uploads 폴더가 생깁니다.

## 자동 점검(11.9절)

```
(.venv) C:\security-lab> pip install bandit pip-audit
(.venv) C:\security-lab> bandit -r app.py
(.venv) C:\security-lab> pip-audit -r requirements.txt
```

## 보안 테스트(11.12절)

조치에 쓸 패키지를 먼저 설치하고 테스트를 실행합니다. 고치기 전에는 26개가 모두 실패합니다.

```
(.venv) C:\security-lab> pip install "PyJWT==2.15.1" "pwdlib[argon2]==0.4.2"
(.venv) C:\security-lab> pytest -q
...
26 failed
```

테스트 이름 앞의 숫자는 진단표의 번호입니다. `pytest -q -k "test_20 or test_03"`처럼 일부만 골라 돌릴 수 있습니다.
테스트를 고쳐서 통과시키면 조치를 한 것이 아닙니다. 고치는 것은 app.py뿐입니다.

### Windows에서 3번 테스트가 다르게 동작할 때

3번(운영체제 명령어 삽입) 테스트는 리눅스 셸에서 명령이 이어서 실행되는지를 확인합니다.
Windows의 명령 프롬프트는 `;`를 명령 구분자로 쓰지 않아 조치하기 전에도 통과할 수 있습니다.
이때는 Docker Desktop을 켜고 리눅스 컨테이너 안에서 테스트를 실행합니다.

```
C:\security-lab> docker run --rm -v "%cd%:/lab" -w /lab python:3.12-slim sh -c "pip install -q -r requirements.txt PyJWT==2.15.1 pwdlib[argon2]==0.4.2 && pytest -q -p no:cacheprovider"
```

## 조치를 마친 뒤

조치를 모두 마치고 11.13절의 테스트 세 개를 직접 추가하면 29개가 모두 통과합니다.
requirements.txt의 requests를 2.34.2로 올리고, PyJWT와 pwdlib도 requirements.txt에 적은 뒤 다시 설치합니다.
solution/requirements.txt와 비교해 봅니다.

```
(.venv) C:\security-lab> pip install -r requirements.txt
(.venv) C:\security-lab> pytest -q
29 passed
(.venv) C:\security-lab> pip-audit -r requirements.txt
No known vulnerabilities found
(.venv) C:\security-lab> bandit -r app.py -ll
No issues identified.
```
