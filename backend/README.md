# 백엔드 (FastAPI)

대화 기록을 받아 파싱·마스킹·감정 분석을 거쳐 결과를 저장하고,
프론트엔드에 JSON으로 돌려주는 API 서버입니다.

## 실행 방법

MySQL이 설치되어 있어야 합니다. 먼저 데이터베이스를 만드세요.

```sql
CREATE DATABASE emotion CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

`.env.example`을 복사해 `.env`를 만들고 본인의 접속 정보를 적습니다.

```bash
python -m venv .venv
.venv\Scripts\activate          # 윈도우
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs (FastAPI가 자동 생성)

테이블은 서버가 처음 뜰 때 자동으로 만들어집니다.

## 폴더 구성

backend/
├── .env 접속 정보 (git에 올리지 않음)
├── .env.example .env 작성용 견본
├── requirements.txt 의존 패키지 목록
└── app/
├── main.py FastAPI 시작점
├── db.py DB 연결
├── models.py DB 테이블 정의
├── schemas.py API 입출력 모양 (Pydantic)
├── routers/ API 주소별 처리 (예정)
└── services/ 파싱·마스킹·분석·후처리 (예정)

## 중요한 규칙

`app/schemas.py`는 **프론트엔드의 `frontend/src/types.ts`와 거울 관계**입니다.
한쪽을 바꾸면 반드시 다른 쪽도 바꾸고 팀에 공유해 주세요.

필드 이름이 `topSub`처럼 파이썬답지 않은 것은 의도한 것입니다.
프론트가 기대하는 JSON 키와 정확히 같아야 하기 때문입니다.

## 처리 흐름

업로드 → 파서 → 마스킹 → 감정 분석 → 후처리 → DB 저장

| 단계 | 하는 일 | 상태 |
|---|---|---|
| 파서 | 파일을 발화 목록으로 변환 (축어록 · CSV · 카톡) | 예정 |
| 마스킹 | 이름·연락처 등 개인정보 가리기 | 예정 |
| 감정 분석 | 발화별 감정 6종 점수 산출 | 예정 |
| 후처리 | 전환점 탐지, 요약 지표 계산 | 예정 |

감정 분석은 **가짜 분석기(랜덤 점수)로 먼저 만들고**, 모델이 준비되면
`services/analyzer.py`의 함수 내부만 교체합니다.
덕분에 모델을 기다리지 않고 전체 흐름을 먼저 완성할 수 있습니다.

## API (예정)

| 요청 | 하는 일 | 쓰는 화면 |
|---|---|---|
| `POST /sessions` | 파일 업로드, 분석 시작 | 화면 1 |
| `GET /sessions/{id}/status` | 진행률 조회 | 화면 2 |
| `GET /sessions/{id}` | 분석 결과 전체 | 화면 3·4 |
| `GET /sessions` | 저장된 분석 목록 | 화면 5 |
| `DELETE /sessions/{id}` | 분석 삭제 | 화면 5 |

## 개인정보 처리

- 업로드된 원본 파일은 저장하지 않습니다. 메모리에서 파싱하고 폐기합니다.
- 전화번호·이메일 등은 저장 전에 마스킹합니다.
- DB에는 마스킹된 발화만 남습니다.

## 현재 상태

- [x] 프로젝트 구조, DB 연결, 테이블 생성
- [x] Pydantic 스키마 (`types.ts`와 대응)
- [ ] 가짜 분석기 + `GET /sessions/{id}`
- [ ] 파서 (축어록 → CSV → 카톡 순)
- [ ] 마스킹
- [ ] 업로드 API + 비동기 처리
- [ ] 실제 모델 연결