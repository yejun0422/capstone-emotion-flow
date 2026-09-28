"""
AI Hub 감성대화 말뭉치에서 문장을 뽑아
화면 3 개발용 더미 분석 결과(dummy.json)를 만든다.

- 문장: 실제 데이터에서 가져옴
- 감정 점수: 모델이 없으므로 그럴듯하게 생성
"""

import json
import random

import pandas as pd

# ---------------------------------------------------------------- 설정

SOURCE_FILE = "train.xlsx"
OUTPUT_FILE = "dummy.json"

SITUATION = "진로,취업,직장"
AGE = "청년"

# 감정을 어떤 순서로 몇 편씩 배치할지
SCRIPT = [("불안", 3), ("슬픔", 3), ("상처", 2), ("불안", 2), ("기쁨", 3)]

EMOTIONS = ["불안", "분노", "상처", "슬픔", "당황", "기쁨"]

# 서로 헷갈리기 쉬운 감정 (점수를 섞어주기 위함)
NEIGHBORS = {
    "불안": ["슬픔", "당황"],
    "분노": ["상처", "당황"],
    "상처": ["슬픔", "분노"],
    "슬픔": ["상처", "불안"],
    "당황": ["불안", "분노"],
    "기쁨": [],
}

WEAK_RATIO = 0.15       # 확신 낮은 추론의 비율
SEED = 42

SESSION_ID = "demo-001"
FILE_NAME = "상담기록_3회기.txt"


# ---------------------------------------------------------------- 함수

def clean(value):
    """빈 칸이나 NaN을 빈 문자열로 통일한다."""
    text = str(value).strip()
    return "" if text in ("", "nan") else text


def pick_conversations(df):
    """감정 대본대로 대화를 골라낸다."""
    pool_all = df[(df["상황키워드"] == SITUATION) & (df["연령"] == AGE)]

    used, picked = set(), []
    for i, (emotion, count) in enumerate(SCRIPT):
        pool = pool_all[
            (pool_all["감정_대분류"] == emotion) & (~pool_all.index.isin(used))
        ]
        rows = pool.sample(count, random_state=SEED + i)
        used.update(rows.index)
        picked.extend(rows.to_dict("records"))
    return picked


def flatten(picked):
    """대화 한 건을 발화 여러 개로 펼친다.

    반환: (발화 목록, 대화별 시작 위치 목록)
    """
    columns = [
        ("사람문장1", "시스템문장1"),
        ("사람문장2", "시스템문장2"),
        ("사람문장3", "시스템문장3"),
    ]

    utterances, blocks = [], []
    index = 1

    for conv in picked:
        start = index
        for human_col, system_col in columns:
            human = clean(conv[human_col])
            if human:
                utterances.append({
                    "index": index,
                    "speaker": "내담자",
                    "text": human,
                    "_emotion": conv["감정_대분류"],
                    "_sub": conv["감정_소분류"],
                })
                index += 1

            system = clean(conv[system_col])
            if system:
                utterances.append({
                    "index": index,
                    "speaker": "상담자",
                    "text": system,
                    "_emotion": None,
                    "_sub": None,
                })
                index += 1
        blocks.append((conv["감정_대분류"], start))

    return utterances, blocks


def make_scores(correct):
    """정답 감정을 중심으로 그럴듯한 점수 벡터를 만든다."""
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


def attach_scores(utterances):
    """각 발화에 감정 점수를 붙이고 임시 키를 정리한다."""
    for u in utterances:
        if u["_emotion"] is None:
            # 상담자 발화는 감정 판단 대상이 아니다
            u["scores"] = None
            u["top"] = None
            u["topSub"] = None
            u["confidence"] = None
        else:
            scores = make_scores(u["_emotion"])
            top = max(scores, key=scores.get)

            u["scores"] = scores
            u["top"] = top
            u["topSub"] = u["_sub"] if top == u["_emotion"] else None
            u["confidence"] = scores[top]

        del u["_emotion"], u["_sub"]


def find_turning_points(blocks):
    """감정이 바뀌는 지점의 발화 번호를 찾는다."""
    return [
        start
        for i, (emotion, start) in enumerate(blocks)
        if i > 0 and emotion != blocks[i - 1][0]
    ]


def summarize(utterances):
    """요약 지표를 계산한다."""
    client = [u for u in utterances if u["speaker"] == "내담자"]
    tops = [u["top"] for u in client]

    changes = sum(1 for a, b in zip(tops, tops[1:]) if a != b)
    low_conf = sum(1 for u in client if u["confidence"] < 0.5)

    return {
        "dominant": max(set(tops), key=tops.count),
        "volatility": round(changes / (len(tops) - 1), 2),
        "lowConfidenceRatio": round(low_conf / len(client), 2),
    }


# ---------------------------------------------------------------- 실행

def main():
    random.seed(SEED)

    df = pd.read_excel(SOURCE_FILE)

    picked = pick_conversations(df)
    utterances, blocks = flatten(picked)
    attach_scores(utterances)

    data = {
        "sessionId": SESSION_ID,
        "fileName": FILE_NAME,
        "speakers": ["상담자", "내담자"],
        "emotions": EMOTIONS,
        "utterances": utterances,
        "turningPoints": find_turning_points(blocks),
        "summary": summarize(utterances),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    client_count = sum(1 for u in utterances if u["speaker"] == "내담자")
    print(f"대화 {len(picked)}편 → 발화 {len(utterances)}개 "
          f"(내담자 {client_count} / 상담자 {len(utterances) - client_count})")
    print("전환점 위치:", data["turningPoints"])
    print("요약:", data["summary"])
    print(f"저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()