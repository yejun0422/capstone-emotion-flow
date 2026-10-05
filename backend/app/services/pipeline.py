"""업로드부터 저장까지의 처리 흐름.

    파싱 → 마스킹 → (분석용 텍스트 정리) → 감정 분석 → 후처리 → DB 저장

DB에는 원문(text)만 저장한다. 괄호류 지문도 원문에 그대로 남는다.
분석용 텍스트는 저장하지 않고, 분석 직전에 text_rules.clean_text()로 만든다.
"""

from sqlalchemy.orm import Session as DBSession

from app.models import SessionRow, UtteranceRow
from app.services import masking, parser, postprocess
from app.services.analyzer import analyze
from app.services.text_rules import clean_text, is_analyzable

BATCH_SIZE = 32


def run(session_id: str, content: bytes, filename: str, counselor: str | None, db: DBSession):
    """분석을 끝까지 수행하고 DB에 저장한다."""
    row = db.get(SessionRow, session_id)

    try:
        # 1. 파싱 — 원문 그대로, 지문 포함
        rows = parser.parse(content, filename)
        names = parser.get_speakers(rows)          # 실명(카톡 등). 역할명은 마스킹에서 제외됨
        rows = parser.map_speakers(rows, counselor)

        # 2. 마스킹
        rows = masking.mask_utterances(rows, names)

        # 3. 분석 대상 고르기 — 내담자 발화 중 지문을 떼고도 내용이 남은 것
        targets = []
        for r in rows:
            if r["speaker"] != "내담자":
                continue
            cleaned = clean_text(r["text"])
            if is_analyzable(cleaned):
                targets.append((r["index"], cleaned))

        row.total = len(targets)
        db.commit()

        # 4. 감정 분석 — 배치로
        scores_by_index: dict[int, dict] = {}
        for i in range(0, len(targets), BATCH_SIZE):
            batch = targets[i : i + BATCH_SIZE]
            results = analyze([text for _, text in batch])
            for (index, _), scores in zip(batch, results):
                scores_by_index[index] = scores

            row.done = min(i + BATCH_SIZE, len(targets))
            db.commit()

        # 5. 후처리
        utterances = []
        for r in rows:
            scores = scores_by_index.get(r["index"])
            top, confidence = postprocess.pick_top(scores)
            utterances.append({
                "index": r["index"],
                "speaker": r["speaker"],
                "text": r["text"],          # 원문 저장
                "scores": scores,
                "top": top,
                "topSub": None,             # 소분류는 모델 연결 후
                "confidence": confidence,
            })

        turning_points = postprocess.find_turning_points(utterances)
        summary = postprocess.summarize(utterances)

        # 6. 저장
        for u in utterances:
            db.add(UtteranceRow(
                session_id=session_id,
                idx=u["index"],
                speaker=u["speaker"],
                text=u["text"],
                scores=u["scores"],
                top=u["top"],
                top_sub=u["topSub"],
                confidence=u["confidence"],
            ))

        row.turning_points = turning_points
        row.summary = summary
        row.status = "done"
        row.done = row.total
        db.commit()

    except Exception as e:
        db.rollback()
        row = db.get(SessionRow, session_id)
        row.status = "failed"
        row.error = str(e)[:500]
        db.commit()