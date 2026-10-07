# 백엔드 (FastAPI)

대화 기록 파일을 받아 파싱·마스킹·감정 분석을 거쳐 결과를 저장하고,
프론트엔드에 JSON으로 돌려주는 API 서버입니다.

---

## 처음 실행할 때

**1. MySQL에 데이터베이스를 만듭니다.** (MySQL Workbench 등에서)

```sql
CREATE DATABASE emotion CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

`utf8mb4`를 꼭 지정하세요. 그냥 `utf8`이면 이모지가 들어올 때 오류가 납니다.

**2. 접속 정보를 적습니다.** `.env.example`을 복사해 `.env`를 만들고 본인 비밀번호를 넣습니다.

```
DATABASE_URL=mysql+pymysql://root:비밀번호@localhost:3306/emotion?charset=utf8mb4
```

**3. 가상환경과 패키지를 준비합니다.** (윈도우 cmd 기준)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**4. 서버를 켭니다.**

```bash
uvicorn app.main:app --reload
```

- 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs (FastAPI가 자동 생성, 여기서 직접 눌러볼 수 있음)

테이블은 서버가 처음 뜰 때 자동으로 만들어집니다.

**5. (선택) 데모 데이터를 넣습니다.**

```bash
python seed.py
```

`frontend/src/data/dummy.json`을 읽어 `demo-001` 세션을 만듭니다.

---

## 폴더 구성

```
backend/
├── .env                    접속 정보 (git에 올리지 않음)
├── .env.example            .env 작성용 견본
├── requirements.txt        의존 패키지 목록
├── seed.py                 dummy.json → DB (개발용, 한 번만 실행)
└── app/
    ├── main.py             FastAPI 시작점, CORS, 라우터 등록
    ├── db.py               DB 연결
    ├── models.py           DB 테이블 정의 (sessions, utterances)
    ├── schemas.py          API 입출력 모양 (Pydantic) — types.ts와 대응
    ├── routers/
    │   └── sessions.py     /sessions 관련 API
    └── services/
        ├── parser.py       파일 → 발화 목록
        ├── text_rules.py   비언어 판별·분석용 텍스트 정리 규칙
        ├── masking.py      개인정보 가리기
        ├── analyzer.py     감정 점수 산출 (현재 임시 구현)
        ├── postprocess.py  대표 감정, 전환점, 요약 지표
        └── pipeline.py     위 단계를 순서대로 실행하고 저장
```

---

## 처리 흐름

```
업로드 → 파싱 → 마스킹 → 분석 대상 고르기 → 감정 분석 → 후처리 → 저장
```

| 단계 | 파일 | 하는 일 |
|---|---|---|
| 파싱 | `parser.py` | 파일을 `{순서, 화자, 원문}` 목록으로 변환 |
| 마스킹 | `masking.py` | 실명·전화번호·이메일 등을 `〈이름〉` 형태로 가림 |
| 분석 대상 고르기 | `pipeline.py` + `text_rules.py` | 내담자 발화 중, 괄호류를 떼고도 내용이 남은 것만 |
| 감정 분석 | `analyzer.py` | 문장마다 감정 6종 점수 |
| 후처리 | `postprocess.py` | 대표 감정·신뢰도, 전환점, 요약 지표 |
| 저장 | `pipeline.py` | 원문과 분석 결과를 DB에 저장 |

분석은 업로드 요청과 별도로 백그라운드에서 돌고, 프론트는 진행률 API를 1초마다 확인합니다.

---

## 파싱 규칙

### 지원 형식

| 형식 | 예시 | 비고 |
|---|---|---|
| 축어록 txt | `상담자 28: 아버지는요?` | 주 대상 |
| CSV | `화자`, `발화` 열 (영문 `speaker`, `text`도 인식) | |
| 카카오톡 txt | `[김상담] [오후 2:01] 내용` | 현 수준 유지, 추가 처리 없음 |

**한 파일에는 한 회기만** 담겨 있다고 가정합니다.

### 화자 표기

- 이름 뒤 번호를 뗍니다. `상담자 28`, `상담자28`, `상담자-28` → `상담자`
- 역할 표기를 통일합니다. `상`, `상담사`, `치료자`, `T` → `상담자` / `내`, `내담`, `환자`, `C` → `내담자`
- 카톡처럼 실명이 화자인 경우 먼저 말한 사람을 상담자로 봅니다.
  업로드 시 `counselor`에 이름을 넘기면 그 사람을 상담자로 지정합니다.

### 비언어 정보 (괄호류)

**원문은 그대로 저장하고, 분석할 때만 떼어냅니다.** 화면에서는 같은 규칙으로 회색 처리합니다.

| 대상 | 예시 |
|---|---|
| 소괄호, 이중 괄호, 전각 괄호 | `(침묵)` `((눈물을 흘리며))` `（웃음）` |
| 대괄호 — 끼어든 상대 발화 | `[상: 그랬군요]` |
| 중괄호 | `{고개를 숙인 채}` |
| 별표 하나로 감싼 것 | `*한숨*` |

남기는 것: 이름 가림 `***`(별표 2개 이상 연속), 작은따옴표 인용 `‘ ’`, 말줄임표 `...`

- **줄 전체가 괄호**이면 직전 발화의 원문 끝에 이어 붙입니다.
- **여러 줄에 걸친 괄호**도 닫는 괄호까지 모아서 직전 발화에 붙입니다.
- 특수 말줄임 문자 `․`(U+2024), `…`(U+2026)는 일반 마침표로 바꿉니다.

> 이 규칙은 `app/services/text_rules.py`에 있고, 프론트의
> `frontend/src/constants/nonverbal.ts`와 **반드시 같이 수정**해야 합니다.

### 분석 대상

- 내담자 발화만 분석합니다. 상담자 발화는 "판단 보류"로 표시됩니다.
- 괄호류를 떼고 난 텍스트가 **5글자 미만이거나 글자가 없으면** 분석하지 않습니다.
  예: `예`, `네`, `......(긴장한 모습)`

### 그 밖의 처리

- 같은 화자의 연속 발화는 최대 3개까지 하나로 합칩니다.
- 발화가 5개 미만이면 형식 오류로 봅니다.
- 인코딩은 UTF-8, CP949(EUC-KR) 순으로 시도합니다.

---

## 개인정보 처리

- 업로드된 원본 파일은 저장하지 않습니다. 메모리에서 처리하고 폐기합니다.
- 저장 전에 다음을 가립니다. 실명(카톡 화자명), 주민번호, 전화번호, 이메일, 계좌번호, 주소
- 가림 표시는 `〈 〉`를 씁니다. `[ ]`를 쓰면 비언어 규칙에 걸려 분석에서 빠지기 때문입니다.

---

## API

| 요청 | 하는 일 | 쓰는 화면 | 상태 |
|---|---|---|---|
| `POST /sessions` | 파일 업로드, 분석 시작. 세션 ID를 즉시 돌려줌 | 화면 1 | ✅ |
| `GET /sessions/{id}/status` | 진행률 (`done` / `total`) | 화면 2 | ✅ |
| `GET /sessions/{id}` | 분석 결과 전체 | 화면 3·4 | ✅ |
| `DELETE /sessions/{id}` | 분석 삭제 | 화면 5 | ✅ |
| `GET /sessions` | 저장된 분석 목록 | 화면 5 | ✅ |

`total`은 전체 발화 수가 아니라 **실제로 분석하는 발화 수**입니다.

---

## 중요한 규칙

`app/schemas.py`는 **프론트엔드의 `frontend/src/types.ts`와 거울 관계**입니다.
한쪽을 바꾸면 반드시 다른 쪽도 바꾸고 팀에 공유해 주세요.

필드 이름이 `topSub`처럼 파이썬답지 않은 것은 의도한 것입니다.
프론트가 기대하는 JSON 키와 정확히 같아야 하기 때문입니다.
DB 쪽(`models.py`)은 파이썬 관례대로 `top_sub`를 쓰고, `routers/sessions.py`에서 변환합니다.

---

## 모델 연결 시

`app/services/analyzer.py`의 `analyze()` 내부만 교체하면 됩니다.

```python
def analyze(texts: list[str]) -> list[dict[str, float]]:
    """문장마다 감정 6종 점수를 돌려준다."""
```

입력은 이미 괄호류가 제거되고 분석 가능한 것만 걸러진 문장입니다.
analyzer는 점수만 내면 되고, 어떤 문장을 분석할지는 신경 쓰지 않아도 됩니다.

---

## 자주 쓰는 작업

**패키지를 새로 설치했을 때** — 목록을 갱신하고 함께 커밋합니다. cmd에서 실행하세요.
PowerShell의 `>`는 UTF-16으로 저장되어 다른 사람이 설치할 때 실패합니다.

```bash
pip install 패키지이름
pip freeze > requirements.txt
```

**DB 데이터를 비울 때** — Workbench의 안전 모드 때문에 그냥 `DELETE`는 막힙니다.
테이블 구조는 남고 데이터만 지워집니다. 순서를 지켜야 합니다.

```sql
USE emotion;
SET SQL_SAFE_UPDATES = 0;
DELETE FROM utterances;
DELETE FROM sessions;
SET SQL_SAFE_UPDATES = 1;
```

**테이블 구조가 바뀌었을 때** — `create_all`은 이미 있는 테이블에 칸을 추가하지 않습니다.
개발 중에는 테이블을 지우고 서버를 다시 켜는 게 가장 간단합니다.

```sql
DROP TABLE utterances;
DROP TABLE sessions;
```

---

## 현재 상태

- [x] 프로젝트 구조, DB 연결, 테이블 생성
- [x] Pydantic 스키마 (`types.ts`와 대응)
- [x] 파서 — 축어록 · CSV · 카톡, 화자 표기 정리, 비언어 정보 분리
- [x] 마스킹
- [x] 업로드 · 진행률 · 결과 조회 · 삭제 API, 백그라운드 처리
- [x] 임시 분석기, 후처리 (대표 감정, 전환점, 요약)
- [x] 세션 목록 API
- [ ] 실제 모델 연결
- [ ] 전환점 알고리즘 튜닝