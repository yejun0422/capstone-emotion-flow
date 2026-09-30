"""업로드부터 저장까지의 처리 흐름.

    파싱 → 마스킹 → 감정 분석 → 후처리 → DB 저장
"""

from sqlalchemy.orm import Session as DBSession

from app.models import SessionRow, UtteranceRow
from app.services import masking, parser, postprocess
from app.services.analyzer import analyze

BATCH_SIZE = 32


def run(session_id: str, content: bytes, filename: str, counselor: str | None, db: DBSession):
    """분석을 끝까지 수행하고 DB에 저장한다."""
    row = db.get(SessionRow, session_id)

    try:
        # 1. 파싱
        rows = parser.parse(content, filename)
        names = parser.get_speakers(rows)
        rows = parser.map_speakers(rows, counselor)

        # 2. 마스킹 (원래 화자 이름도 본문에서 가린다)
        rows = masking.mask_utterances(rows, names)

        row.total = len(rows)
        db.commit()

        # 3. 감정 분석 — 내담자 발화만, 배치로 나눠서
        targets = [r for r in rows if r["speaker"] == "내담자"]
        scores_by_index: dict[int, dict | None] = {}

        for i in range(0, len(targets), BATCH_SIZE):
            batch = targets[i : i + BATCH_SIZE]
            results = analyze([b["text"] for b in batch])
            for item, scores in zip(batch, results):
                scores_by_index[item["index"]] = scores

            row.done = min(i + BATCH_SIZE, len(targets))
            db.commit()

        # 4. 후처리
        utterances = []
        for r in rows:
            scores = scores_by_index.get(r["index"])
            top, confidence = postprocess.pick_top(scores)
            utterances.append(
                {
                    "index": r["index"],
                    "speaker": r["speaker"],
                    "text": r["text"],
                    "scores": scores,
                    "top": top,
                    "topSub": None,      # 소분류는 모델 연결 후
                    "confidence": confidence,
                }
            )

        turning_points = postprocess.find_turning_points(utterances)
        summary = postprocess.summarize(utterances)

        # 5. 저장
        for u in utterances:
            db.add(
                UtteranceRow(
                    session_id=session_id,
                    idx=u["index"],
                    speaker=u["speaker"],
                    text=u["text"],
                    scores=u["scores"],
                    top=u["top"],
                    top_sub=u["topSub"],
                    confidence=u["confidence"],
                )
            )

        row.turning_points = turning_points
        row.summary = summary
        row.status = "done"
        row.done = row.total
        db.commit()

    except Exception as e:
        row.status = "failed"
        row.error = str(e)[:500]
        db.commit()