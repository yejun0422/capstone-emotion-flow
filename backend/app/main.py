from fastapi import FastAPI

from app.db import SessionLocal, engine
from app.models import Base
from app.routers import auth, sessions
from app.services.analyzer import load_model
from app.services.pipeline import fail_unfinished

Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    fail_unfinished(db)   # 지난번에 서버가 꺼지면서 멈춘 분석을 실패로 정리

load_model()  # 감정 모델은 서버가 켜질 때 한 번만 불러 둔다

app = FastAPI(title="감정 흐름 분석 API")

app.include_router(auth.router)
app.include_router(sessions.router)


@app.get("/health")
def health():
    return {"ok": True}