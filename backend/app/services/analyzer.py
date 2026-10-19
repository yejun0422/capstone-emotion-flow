"""
감정 분석기.

문장 목록을 받아 문장마다 감정 6종 점수를 돌려주는 일만 한다.
어떤 문장을 분석할지(지문 제거, 짧은 발화 제외)는 pipeline이 정한다.

모델(KcELECTRA 멀티태스크)을 불러오는 일은 emotion_model.py가 하고,
여기서는 서버가 켜질 때 한 번만 불러 두고 계속 쓴다.
"""

from app.services.emotion_model import EmotionClassifier

EMOTIONS = ["불안", "분노", "상처", "슬픔", "당황", "기쁨"]

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