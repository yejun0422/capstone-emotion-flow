"""
감정 분석기.

문장 목록을 받아 문장마다 감정 6종 점수를 돌려주는 일만 한다.
어떤 문장을 분석할지(지문 제거, 짧은 발화 제외)는 pipeline이 정한다.

지금은 랜덤 점수를 돌려주는 가짜 구현이다.
모델이 준비되면 analyze() 함수 내부만 교체한다.
"""

import random

EMOTIONS = ["불안", "분노", "상처", "슬픔", "당황", "기쁨"]

NEIGHBORS = {
    "불안": ["슬픔", "당황"],
    "분노": ["상처", "당황"],
    "상처": ["슬픔", "분노"],
    "슬픔": ["상처", "불안"],
    "당황": ["불안", "분노"],
    "기쁨": [],
}

WEAK_RATIO = 0.15


def analyze(texts: list[str]) -> list[dict[str, float]]:
    """문장마다 감정 6종 점수를 돌려준다."""
    return [_fake_scores() for _ in texts]


def _fake_scores() -> dict[str, float]:
    correct = random.choice(EMOTIONS)
    weak = random.random() < WEAK_RATIO

    scores = {}
    for emotion in EMOTIONS:
        if emotion == correct:
            low, high = (0.30, 0.50) if weak else (0.65, 0.90)
        elif emotion in NEIGHBORS[correct]:
            low, high = 0.20, 0.50
        else:
            low, high = 0.00, 0.15
        scores[emotion] = round(random.uniform(low, high), 2)
    return scores