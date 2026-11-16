# 감정 분석 모델 사용 안내 (LLM 기반: EXAONE)

기존 KcELECTRA 모델과 **같은 형식의 결과**(대표 감정 6개 점수, 세부 감정 등)를 반환하는 LLM 기반 모델입니다.
기존 KcELECTRA 파일은 그대로 두고, LLM 파일을 **옆에 추가**하는 방식으로 구성했습니다.

## 1. 파일별 역할

프로젝트 폴더에 아래 구조로 배치합니다. (기존 KcELECTRA 파일은 그대로 둡니다.)

``` text
프로젝트/
├── model/
│   ├── final_kcelectra_multitask_config.json     (기존 KcELECTRA)
│   ├── final_kcelectra_multitask_tokenizer/      (기존 KcELECTRA)
│   ├── result/                                   (기존 KcELECTRA 평가 결과)
│   └── llm_exaone/                               ← LLM 모델 (새로 추가)
│       ├── adapter/
│       │   ├── lora_and_heads.pt
│       │   └── lora_config.json
│       ├── tokenizer/
│       ├── config.json
│       ├── label_mapping.json
│       ├── evaluation_result.json
│       └── versions.json
└── backend/
    └── app/
        └── services/
            ├── emotion_model.py                  (기존 KcELECTRA 로더)
            └── emotion_model_llm.py              ← LLM 로더 (새로 추가)
```

-   `emotion_model_llm.py`: LLM 기반 한국어 감정 분석 모델 로더. 클래스 이름(`EmotionClassifier`),
    `predict()`, `predict_many()`, 반환 형식이 기존 `emotion_model.py`와 같습니다.
-   `adapter/lora_and_heads.pt`: 학습된 가중치(LoRA 어댑터 + 감정 분류 헤드, 약 59MB)
-   `adapter/lora_config.json`: LoRA 설정
-   `tokenizer/`: 입력 문장을 모델 입력(숫자)으로 변환하는 토크나이저 파일
-   `config.json`: 기반 모델 이름, 감정 라벨, 최대 입력 길이, 평가 결과 요약 등 설정
-   `label_mapping.json`: 대분류 6개, 소분류 58개 라벨 매핑
-   `evaluation_result.json`: 검증 데이터 평가 결과(대분류/소분류 Macro-F1, 정확도, 신뢰구간 등)
-   `versions.json`: 학습에 사용한 라이브러리 버전

### 모델 구성

-   기반 모델: `LGAI-EXAONE/EXAONE-4.0-1.2B` (약 12.8억 파라미터)
-   학습 방식: LoRA(r=16) + 대분류(6개)/소분류(58개) 분류 헤드, 학습 데이터 51,630개로 2 epoch 학습
-   입력: 사용자(내담자) 발화 2~3개를 공백으로 이어 붙인 텍스트 (KcELECTRA와 같은 입력 방식)
-   출력: 감정별 확률(softmax)

## *** 가중치 파일 다운로드 ***

어댑터 가중치 파일인 lora_and_heads.pt의 용량이 커서 업로드가 막혔습니다.
아래의 Google Drive 공유 링크에서 파일을 다운로드한 후, 본인 작업 환경의 model/llm_exaone/adapter/ 디렉터리에 저장해 주세요.

https://drive.google.com/file/d/1JmIH9-fum_VNVluLNzkiA7EqNON6LRyq/view?usp=sharing

## 2. 설치

LLM 사용에는 아래 패키지가 필요합니다. (기존 KcELECTRA는 `torch`, `transformers`만 필요했습니다.)

``` text
torch
transformers>=4.54
peft
```

``` bash
pip install peft
pip install -U "transformers>=4.54"
```

-   `transformers`가 **4.54 이상**이어야 모델 구조(EXAONE 4.0)를 인식합니다.


## 3. 기본 사용법

프로젝트 루트 폴더에서 실행 시

``` python
from backend.app.services.emotion_model_llm import EmotionClassifier

classifier = EmotionClassifier()   # model/llm_exaone 폴더를 자동으로 찾음

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


`predict`와 `predict_many`는 KcELECTRA와 같은 형식으로 아래 항목을 반환합니다.
`text`, `major_emotion`, `major_probability`, `major_scores`(6개 감정 점수),
`minor_emotion`, `minor_probability`, `major_top_k`, `minor_top_k`.

## 4. 기존 `analyzer.py`와 연결 예시 코드

`analyze(texts)`의 코드는 KcELECTRA 때와 **같습니다.** import 한 줄만 바꾸면 모델이 바뀝니다.

``` python
# KcELECTRA (기존)
from emotion_model import EmotionClassifier
# LLM으로 교체할 때 (위 줄 대신 아래 줄 사용)
# from emotion_model_llm import EmotionClassifier

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

한 파일에서 두 모델을 **동시에** 쓰려면 클래스 이름이 겹치므로 별칭을 사용합니다.

``` python
from emotion_model import EmotionClassifier as KcElectraClassifier
from emotion_model_llm import EmotionClassifier as LLMEmotionClassifier
```

사용 예시
``` python
analyze(["오늘은 정말 기분이 좋다.",
         "오늘 발표를 망쳐서 정말 속상했어요."])
```
실행 결과 (LLM 모델)
``` 
[{'불안': 0.0, '분노': 0.0, '상처': 0.0, '슬픔': 0.0, '당황': 0.0, '기쁨': 1.0},
 {'불안': 0.03, '분노': 0.08, '상처': 0.09, '슬픔': 0.69, '당황': 0.09, '기쁨': 0.01}]
```

## 5. 성능

평가 데이터: AI Hub 감성대화말뭉치 **검증 데이터 6,641개** (KcELECTRA와 같은 데이터, 같은 입력, 같은 지표)

| 모델 | 대분류 Macro-F1 | 비고                                                   |
|---|---|------------------------------------------------------|
| **EXAONE (이 모델)** | **0.7671** | 정확도 0.7726, Weighted-F1 0.7730, 95% 구간 0.7575~0.7778 |
| KcELECTRA (기존 모델) | 0.7654 | 이전에 측정한 값                                            |
| 공개 KcELECTRA 모델 (GGARA02) | 0.7711 | 우리 검증 데이터로 직접 평가                                     |
| Qwen3-1.7B (비교 실험) | 0.7594 | 같은 방식으로 학습                                           |

-   EXAONE 소분류(58개) Macro-F1: 0.5301


### 성능 해석 시 주의
-   Hugging Face에서 0.86 정도의 성능을 낸 KcELECTRA 사례(GGARA02)가 있으나, 이는 출처가 설명되지 않은
    별도의 test 데이터 5,135개로 평가한 값입니다. 같은 모델을 우리 검증 데이터로 평가하면 0.7711이었습니다.
-   AI Hub 검증 데이터의 약 38%는 학습 데이터(Train)와 매우 비슷한 문장입니다(유사도 0.5 이상, 약 29%는 0.8 이상).
    Train 내부에서 이런 비율은 약 3.5%여서, 검증 데이터가 학습 데이터와 유난히 많이 겹칩니다.
    그래서 **전체 점수는 새로운 문장에 대한 성능보다 높게 나옵니다.**
-   Train과 유사도가 낮은(0.5 미만) 문장 4,131개만 평가하면 대분류 Macro-F1은 EXAONE 0.7240,
    공개 KcELECTRA 모델 0.7156으로, **실제 상담 기록에서는 EXAONE이 공개 KcELECTRA보다 좋은 성능을
    보일 것으로 예상됩니다.**

## 6. 속도와 메모리

일반 노트북 CPU(NVIDIA GPU 없음, RAM 12GB)에서 문장 하나가 짧은 한 줄(약 40자)일 때 측정한 값입니다.

| | KcELECTRA | EXAONE (이 모델) |
|---|---|---|
| 메모리 | 약 1.3GB | 약 4.1GB |
| 1문장 | 0.07~0.1초 | 약 0.8~1.2초 |
| 16문장 한 번에 | 0.4초 | 6.0~6.4초 |
| 문장당 | 약 0.02초 | 약 0.4초 |
| 200문장(계산값) | 약 4초 | **약 80초** |

-   EXAONE은 KcELECTRA보다 **약 20배 느립니다.** 200문장은 측정한 값이 아니라 문장당 시간으로 계산한 값이며,
    문장이 더 길면 더 걸립니다.


## 7. 서버로 사용할 때 주의

-   모델은 **서버 시작 때 한 번만** 불러오세요. (`EmotionClassifier()` 생성이 로딩입니다.)
    위 `analyze()`처럼 처음 호출될 때 로딩하면 첫 요청이 오래 걸리므로, 서버 시작 시 `analyze(["준비"])`를
    한 번 호출해 두는 것을 권합니다. 첫 예측에서 메모리가 실제로 늘어나기 때문에, 로딩만 하고 예측은 하지 않으면
    첫 요청에서 느려질 수 있습니다.
-   서버 프로세스(워커)는 **1개**로 시작하세요. 프로세스마다 모델(약 4GB)이 따로 올라갑니다.
-   개발 중 자동 재시작(`--reload`)을 켜면 저장할 때마다 모델이 다시 올라가 메모리가 쌓일 수 있습니다.
-   KcELECTRA와 LLM을 동시에 올리면 메모리를 합쳐서 사용합니다(약 5.5GB)
-   `device="cuda"`는 NVIDIA GPU가 있는 컴퓨터에서만 사용하세요. 지정하지 않으면 자동으로 선택됩니다.

## 8. 라이선스

-   기반 모델 EXAONE-4.0-1.2B는 **비상업적 용도(연구, 교육)에서만** 사용할 수 있습니다
    (EXAONE AI Model License 1.2-NC). 이 어댑터는 해당 모델을 기반으로 학습한 파생물이므로
    같은 조건을 따릅니다. 상업적 이용 시에는 라이선스 원문을 확인해 주세요.

