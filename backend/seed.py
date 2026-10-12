"""
frontend/src/data/dummy.json을 읽어 DB에 넣는다.
시연용 계정(demo)을 만들고, 데모 세션(demo-001)을 그 계정 소유로 저장한다.
개발용으로 한 번만 실행하면 된다. 여러 번 실행해도 결과는 같다.

    python seed.py

시연 계정 비밀번호는 .env의 DEMO_PASSWORD에서 읽는다.
"""

import json
import os
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal, engine
from app.models import Base, SessionRow, UserRow, UtteranceRow
from app.services.auth import hash_password

DUMMY_PATH = Path(__file__).parent.parent / "frontend" / "src" / "data" / "dummy.json"
SESSION_ID = "demo-001"
DEMO_USERNAME = "demo"


def main():
    demo_password = os.getenv("DEMO_PASSWORD")
    if not demo_password:
        raise SystemExit("DEMO_PASSWORD가 없습니다. backend/.env에 시연 계정 비밀번호를 적어 주세요.")

    Base.metadata.create_all(bind=engine)

    with open(DUMMY_PATH, encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        # 시연 계정: 없으면 만들고, 있으면 비밀번호만 .env 값으로 맞춘다
        user = db.scalar(select(UserRow).where(UserRow.username == DEMO_USERNAME))
        if user is None:
            user = UserRow(username=DEMO_USERNAME, password_hash=hash_password(demo_password))
            db.add(user)
        else:
            user.password_hash = hash_password(demo_password)
        db.commit()
        db.refresh(user)

        # 같은 id가 이미 있으면 지우고 다시 넣는다
        existing = db.get(SessionRow, SESSION_ID)
        if existing:
            db.delete(existing)
            db.commit()

        row = SessionRow(
            id=SESSION_ID,
            file_name=data["fileName"],
            status="done",
            total=len(data["utterances"]),
            done=len(data["utterances"]),
            summary=data["summary"],
            turning_points=data["turningPoints"],
            user_id=user.id,
        )
        db.add(row)

        for u in data["utterances"]:
            db.add(
                UtteranceRow(
                    session_id=SESSION_ID,
                    idx=u["index"],
                    speaker=u["speaker"],
                    text=u["text"],
                    scores=u["scores"],
                    top=u["top"],
                    top_sub=u["topSub"],
                    confidence=u["confidence"],
                )
            )

        db.commit()
        print(f"저장 완료: {SESSION_ID} — 발화 {len(data['utterances'])}개, 계정 '{DEMO_USERNAME}' 소유")
    finally:
        db.close()


if __name__ == "__main__":
    main()