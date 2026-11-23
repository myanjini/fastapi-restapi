from fastapi import FastAPI

app = FastAPI(title="도서 관리 API")

@app.get("/")
def read_root():
    return {"message": "도서 관리 API에 오신 것을 환영합니다."}

@app.get("/health")
def health_check():
    # 서버가 요청에 응답할 수 있는지 확인하는 용도입니다.
    return {"status": "ok"}
