"""
frontend/src/data/dummy.json을 읽어 DB에 넣는다.
개발용으로 한 번만 실행하면 된다.

    python seed.py
"""

import json
from pathlib import Path

from app.db import SessionLocal, engine
from app.models import Base, SessionRow, UtteranceRow

DUMMY_PATH = Path(__file__).parent.parent / "frontend" / "src" / "data" / "dummy.json"
SESSION_ID = "demo-001"


def main():
    Base.metadata.create_all(bind=engine)

    with open(DUMMY_PATH, encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
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
        print(f"저장 완료: {SESSION_ID} — 발화 {len(data['utterances'])}개")
    finally:
        db.close()


if __name__ == "__main__":
    main()