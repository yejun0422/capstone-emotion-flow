from fastapi import FastAPI
from .db import engine
from .models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True}