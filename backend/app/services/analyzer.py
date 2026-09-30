"""
감정 분석기.

지금은 랜덤 점수를 돌려주는 가짜 구현이다.
모델이 준비되면 analyze() 함수 내부만 교체하면 되고,
호출하는 쪽은 바꿀 필요가 없다.
"""

import random

EMOTIONS = ["불안", "분노", "상처", "슬픔", "당황", "기쁨"]

# 서로 헷갈리기 쉬운 감정
NEIGHBORS = {
    "불안": ["슬픔", "당황"],
    "분노": ["상처", "당황"],
    "상처": ["슬픔", "분노"],
    "슬픔": ["상처", "불안"],
    "당황": ["불안", "분노"],
    "기쁨": [],
}

WEAK_RATIO = 0.15      # 확신이 낮은 추론의 비율
MIN_LENGTH = 5         # 이보다 짧은 발화는 분석하지 않음


def analyze(texts: list[str]) -> list[dict[str, float] | None]:
    """발화 목록을 받아 발화마다 감정 6종 점수를 돌려준다.

    분석할 수 없는 발화(너무 짧음)는 None을 돌려준다.
    """
    return [_fake_scores(t) for t in texts]


def _fake_scores(text: str) -> dict[str, float] | None:
    if len(text.strip()) < MIN_LENGTH:
        return None

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