"""
감정 분석기.

문장 목록을 받아 문장마다 감정 6종 점수를 돌려주는 일만 한다.
어떤 문장을 분석할지(지문 제거, 짧은 발화 제외)는 pipeline이 정한다.

모델(KcELECTRA 멀티태스크)을 불러오는 일은 emotion_model.py가 하고,
여기서는 서버가 켜질 때 한 번만 불러 두고 계속 쓴다.
"""

from app.services.emotion_model import EmotionClassifier

EMOTIONS = ["불안", "분노", "상처", "슬픔", "당황", "기쁨"]

# 이전 내담자 발화와 묶어서 넣은 점수의 비중. 나머지(0.7)는 현재 발화만 넣은 점수.
# 샘플 10편으로 0.5 / 0.6 / 0.7을 비교해 정함 (0.5는 전환이 늦게 잡히고 기존보다 나빠짐)
CONTEXT_WEIGHT = 0.3

_classifier: EmotionClassifier | None = None


def load_model() -> None:
    """모델을 불러 둔다. 서버 시작 때 main.py에서 한 번 부른다."""
    global _classifier
    if _classifier is None:
        _classifier = EmotionClassifier()


def analyze(texts: list[str]) -> list[dict[str, float]]:
    """문장마다 감정 6종 점수(합이 1인 확률)를 돌려준다."""
    load_model()   # 아직 안 불러왔으면 여기서 불러온다
    results = _classifier.predict_many(texts)
    return [
        {emotion: round(r["major_scores"][emotion], 4) for emotion in EMOTIONS}
        for r in results
    ]


def analyze_with_context(texts: list[str], previous: list[str | None]) -> list[dict[str, float]]:
    """현재 발화만 넣은 점수와, 이전 내담자 발화를 앞에 붙여 넣은 점수를 섞는다.

    previous[i]는 texts[i] 바로 앞의 내담자 발화(첫 발화는 None).
    다음 발화는 쓰지 않는다. 감정은 시간 순서대로 생기기 때문이다.
    """
    single = analyze(texts)
    joined = [f"{p} {t}" if p else t for p, t in zip(previous, texts)]
    context = analyze(joined)
    w = CONTEXT_WEIGHT
    return [
        {e: round((1 - w) * s[e] + w * c[e], 4) for e in EMOTIONS}
        for s, c in zip(single, context)
    ]