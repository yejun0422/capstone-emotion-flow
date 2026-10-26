"""감정 점수로부터 대표 감정, 전환점, 요약 지표를 계산한다."""

from app.services.analyzer import EMOTIONS

MIXED_THRESHOLD = 0.7


def pick_top(scores: dict[str, float] | None) -> tuple[str | None, float | None]:
    """가장 높은 감정과 그 점수를 돌려준다."""
    if not scores:
        return None, None
    top = max(scores, key=scores.get)
    return top, scores[top]


def find_turning_points(utterances: list[dict], window: int = 3, threshold: float = 0.5) -> list[int]:
    """감정 흐름이 크게 바뀌는 지점의 발화 번호를 찾는다.

    분석된 내담자 발화를 순서대로 보며, 어떤 발화를 기준으로
    앞쪽 window개와 뒤쪽 window개의 평균 감정 분포가 얼마나 다른지(0~1) 계산한다.
    그 차이가 threshold 이상이면서 이웃보다 큰 곳(봉우리)을 전환점으로 본다.
    """
    targets = [u for u in utterances if u["scores"]]
    if len(targets) < window * 2:
        return []

    # 기준 발화 i: 앞쪽 [i-window, i), 뒤쪽 [i, i+window)
    diffs: dict[int, float] = {}
    for i in range(window, len(targets) - window + 1):
        before = _mean_scores(targets[i - window : i])
        after = _mean_scores(targets[i : i + window])
        diffs[i] = 0.5 * sum(abs(before[e] - after[e]) for e in EMOTIONS)

    # 봉우리: 기준 이상이고, 왼쪽 이웃보다 크고, 오른쪽 이웃보다 작지 않은 곳
    peaks = [
        i for i, d in diffs.items()
        if d >= threshold and d > diffs.get(i - 1, -1.0) and d >= diffs.get(i + 1, -1.0)
    ]

    # window보다 가까이 붙은 봉우리는 더 높은 쪽 하나만 남긴다
    chosen: list[int] = []
    for i in peaks:
        if chosen and i - chosen[-1] < window:
            if diffs[i] > diffs[chosen[-1]]:
                chosen[-1] = i
            continue
        chosen.append(i)

    return [targets[i]["index"] for i in chosen]


def _mean_scores(items: list[dict]) -> dict[str, float]:
    """구간의 감정별 평균 점수."""
    return {e: sum(it["scores"][e] for it in items) / len(items) for e in EMOTIONS}


def _dominant(targets: list[dict]) -> str:
    """1등으로 가장 많이 나온 감정. 동점이면 평균 점수가 높은 감정.

    동점을 set 순서에 맡기면 서버를 켤 때마다 다른 감정이 나올 수 있어서 기준을 정해 둔다.
    """
    tops = [u["top"] for u in targets]
    mean = _mean_scores(targets)
    return max(EMOTIONS, key=lambda e: (tops.count(e), mean[e]))


def summarize(utterances: list[dict]) -> dict:
    """요약 지표를 계산한다."""
    targets = [u for u in utterances if u["top"]]
    if not targets:
        return {"dominant": "불안", "volatility": 0.0, "mixedRatio": 0.0}

    tops = [u["top"] for u in targets]
    changes = sum(1 for a, b in zip(tops, tops[1:]) if a != b)
    mixed = sum(1 for u in targets if u["confidence"] < MIXED_THRESHOLD)

    return {
        "dominant": _dominant(targets),
        "volatility": round(changes / (len(tops) - 1), 2) if len(tops) > 1 else 0.0,
        "mixedRatio": round(mixed / len(targets), 2),
    }