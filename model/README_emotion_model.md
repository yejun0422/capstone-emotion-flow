# 감정 분석 모델 사용 안내

## 1. 파일별 역할

프로젝트 폴더에 아래 구조로 배치합니다.

``` text
프로젝트/
├── model/
│   ├── final_kcelectra_multitask.pt
│   ├── final_kcelectra_multitask_config.json
│   ├── final_kcelectra_multitask_tokenizer/
│   └── result/
└── backend/
    └── app/
        └── services/
            └── emotion_model.py
```

-   `emotion_model.py`: KcELECTRA 기반 한국어 감정 분석 모델 로더
-   `final_kcelectra_multitask.pt`: 학습된 모델 가중치
-   `final_kcelectra_multitask_config.json`: 모델 이름, 감정 라벨, 최대
    입력 길이 등 설정
-   `final_kcelectra_multitask_tokenizer/`: 입력 문장(한국어)을 모델 입력 형태(숫자)로
    변환하는 토크나이저 파일
-   `result/`: 모델 학습 후 성능 평가 결과, major_macro_f1: 0.7654 가 나옴

`emotion_model.py`는 analyzer.py에서 바로 import 할 수 있도록 backend/app/services/에 위치시켰습니다.

## *** 모델 가중치 파일 다운로드 ***

모델 가중치 파일인 final_kcelectra_multitask.pt의 용량이 커서 업로드가 막혔습니다.
아래의 Google Drive 공유 링크에서 파일을 다운로드한 후, 본인 작업 환경의 model/ 디렉터리에 저장해 주세요.

https://drive.google.com/file/d/15_JJpmD2FDHOGJZexlk65LVsVOrKcwGr/view?usp=sharing

모델이 정상적으로 작동하려면 final_kcelectra_multitask.pt 파일을 model/ 디렉터리에 위치시켜야 합니다.

## 2. 기본 사용법

프로젝트 루트 폴더에서 실행 시

``` python
from backend.app.services.emotion_model import EmotionClassifier

classifier = EmotionClassifier()

# 문장 하나
result = classifier.predict("오늘은 정말 기분이 좋다.")
print(result["major_emotion"])
print(result["major_scores"])

# 여러 문장
results = classifier.predict_many([
    "오늘은 정말 기분이 좋다.",
    "오늘 발표를 망쳐서 정말 속상했어요."
])
```

predict와 predict_many는 주요 감정의 점수 이외에도 세부 감정의 점수, text 등의 세부 정보들을 반환합니다.

## 3. 기존 `analyzer.py`와 연결 예시 코드

기존 analyzer.py의 `analyze(texts)` 반환 형식을 유지하려면, 각 문장 결과에서
`major_scores`만 추출하면 됩니다.

``` python
from emotion_model import EmotionClassifier

EMOTIONS = ["불안", "분노", "상처", "슬픔", "당황", "기쁨"]

# 모델을 매번 새로 로드하지 않도록 한 번만 생성
_classifier = None


def analyze(texts: list[str]) -> list[dict[str, float]]:
    """문장마다 6개 대표 감정의 점수를 소수점 둘째 자리까지 반환한다."""
    global _classifier

    if _classifier is None:
        _classifier = EmotionClassifier()

    results = _classifier.predict_many(texts)

    return [
        {
            emotion: round(float(result["major_scores"][emotion]), 2)
            for emotion in EMOTIONS
        }
        for result in results
    ]
```
사용 예시
``` python
text = ["오늘 발표를 망쳐서 정말 속상했어요.",
        "친구가 도와줘서 마음이 한결 편해졌어요.",]
analyze(text)
```
실행 결과
``` 
[{'불안': 0.0, '분노': 0.0, '상처': 0.0, '슬픔': 0.0, '당황': 0.0, '기쁨': 0.99},
 {'불안': 0.05, '분노': 0.08, '상처': 0.05, '슬픔': 0.71, '당황': 0.12, '기쁨': 0.0}]
```



-   `analyze(texts)`: 문장별 대표 감정 6개 점수만 반환
-   `classifier.predict_many(texts)`: 대표 감정, 6개 점수, 세부 감정 및
    상위 예측 결과 등 전체 결과 반환
-   세부 감정이 필요하면 `predict_many()` 결과의 `minor_emotion`,
    `minor_top_k` 등을 사용하면 됩니다.



