import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session as DBSession

from app.db import SessionLocal, get_db
from app.models import SessionRow
from app.schemas import Session, SessionStatusResponse, Summary, Utterance
from app.services.analyzer import EMOTIONS
from app.services.pipeline import run

router = APIRouter(prefix="/sessions", tags=["sessions"])

MAX_SIZE = 5 * 1024 * 1024   # 5MB


@router.post("", response_model=SessionStatusResponse, status_code=202)
async def create_session(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    counselor: str | None = Form(None),
    db: DBSession = Depends(get_db),
):
    """파일을 받아 분석을 시작한다. 즉시 세션 ID를 돌려준다. (화면 1)"""
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="파일이 너무 큽니다. (최대 5MB)")
    if not content:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    session_id = str(uuid.uuid4())
    db.add(
        SessionRow(
            id=session_id,
            file_name=file.filename or "unknown.txt",
            status="processing",
        )
    )
    db.commit()

    background.add_task(_run_in_background, session_id, content, file.filename or "", counselor)

    return SessionStatusResponse(
        sessionId=session_id, status="processing", done=0, total=0
    )


def _run_in_background(session_id: str, content: bytes, filename: str, counselor: str | None):
    """백그라운드 작업은 자기만의 DB 연결을 써야 한다."""
    db = SessionLocal()
    try:
        run(session_id, content, filename, counselor, db)
    finally:
        db.close()


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
def get_status(session_id: str, db: DBSession = Depends(get_db)):
    """분석 진행률을 돌려준다. (화면 2)"""
    row = db.get(SessionRow, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")

    return SessionStatusResponse(
        sessionId=row.id, status=row.status, done=row.done, total=row.total
    )


@router.get("/{session_id}", response_model=Session)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    """분석 결과 전체를 돌려준다. (화면 3·4)"""
    row = db.get(SessionRow, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    if row.status == "failed":
        raise HTTPException(status_code=422, detail=row.error or "분석에 실패했습니다.")
    if row.status != "done":
        raise HTTPException(status_code=409, detail="아직 분석 중입니다.")

    return Session(
        sessionId=row.id,
        fileName=row.file_name,
        speakers=["상담자", "내담자"],
        emotions=EMOTIONS,
        utterances=[
            Utterance(
                index=u.idx,
                speaker=u.speaker,
                text=u.text,
                scores=u.scores,
                top=u.top,
                topSub=u.top_sub,
                confidence=u.confidence,
            )
            for u in row.utterances
        ],
        turningPoints=row.turning_points or [],
        summary=Summary(**row.summary),
    )


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    """분석을 삭제한다. (화면 5)"""
    row = db.get(SessionRow, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
    db.delete(row)
    db.commit()