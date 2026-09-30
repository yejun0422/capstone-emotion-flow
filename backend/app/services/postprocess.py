"""감정 점수로부터 대표 감정, 전환점, 요약 지표를 계산한다."""

from app.services.analyzer import EMOTIONS

LOW_CONFIDENCE = 0.5


def pick_top(scores: dict[str, float] | None) -> tuple[str | None, float | None]:
    """가장 높은 감정과 그 점수를 돌려준다."""
    if not scores:
        return None, None
    top = max(scores, key=scores.get)
    return top, scores[top]


def find_turning_points(utterances: list[dict], window: int = 3) -> list[int]:
    """감정 흐름이 크게 바뀌는 지점의 발화 번호를 찾는다.

    어떤 발화를 기준으로 앞쪽 window개의 평균 감정과
    뒤쪽 window개의 평균 감정을 비교해, 대표 감정이 달라지면 전환점으로 본다.
    """
    targets = [u for u in utterances if u["scores"]]
    if len(targets) < window * 2:
        return []

    points = []
    for i in range(window, len(targets) - window):
        before = _mean_top(targets[i - window : i])
        after = _mean_top(targets[i : i + window])
        if before != after:
            points.append(targets[i]["index"])

    return _merge_close(points, min_gap=window * 2)


def _mean_top(items: list[dict]) -> str:
    """구간의 평균 감정 중 가장 강한 것."""
    total = {e: 0.0 for e in EMOTIONS}
    for item in items:
        for emotion, score in item["scores"].items():
            total[emotion] += score
    return max(total, key=total.get)


def _merge_close(points: list[int], min_gap: int) -> list[int]:
    """가까이 붙은 전환점은 첫 번째만 남긴다."""
    merged = []
    for p in points:
        if not merged or p - merged[-1] >= min_gap:
            merged.append(p)
    return merged


def summarize(utterances: list[dict]) -> dict:
    """요약 지표를 계산한다."""
    targets = [u for u in utterances if u["top"]]
    if not targets:
        return {"dominant": "불안", "volatility": 0.0, "lowConfidenceRatio": 0.0}

    tops = [u["top"] for u in targets]
    changes = sum(1 for a, b in zip(tops, tops[1:]) if a != b)
    low = sum(1 for u in targets if u["confidence"] < LOW_CONFIDENCE)

    return {
        "dominant": max(set(tops), key=tops.count),
        "volatility": round(changes / (len(tops) - 1), 2) if len(tops) > 1 else 0.0,
        "lowConfidenceRatio": round(low / len(targets), 2),
    }