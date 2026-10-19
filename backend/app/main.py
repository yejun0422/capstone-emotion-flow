from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine
from app.models import Base
from app.routers import auth, sessions
from app.services.analyzer import load_model

Base.metadata.create_all(bind=engine)

load_model()  # 감정 모델은 서버가 켜질 때 한 번만 불러 둔다

app = FastAPI(title="감정 흐름 분석 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sessions.router)


@app.get("/health")
def health():
    return {"ok": True}