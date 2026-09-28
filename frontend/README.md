# 감정 흐름 분석 — 프론트엔드

상담·대화 기록을 올리면 발화 순서에 따른 감정 변화를 곡선으로 보여주고,
감정이 크게 바뀐 지점(전환점)을 표시하는 웹 화면입니다.

2026-2학기 산학캡스톤디자인 · 팀 안성맞춤

## 실행 방법

Node.js 20 이상이 필요합니다.

```bash
npm install     # 처음 한 번만
npm run dev     # 개발 서버 실행 → http://localhost:5173
```

그 밖의 명령어입니다.

| 명령어 | 하는 일 |
|---|---|
| `npm run build` | 타입 검사 후 배포용 파일을 `dist/`에 생성 |
| `npm run lint` | 코드 검사 (Oxlint) |
| `npm run preview` | 빌드 결과를 로컬에서 미리 보기 |

## 폴더 구조

```
src/
├── main.tsx              앱 시작점 (건드릴 일 없음)
├── App.tsx               화면 3 조립 + 상태 관리
├── index.css             Tailwind 불러오기
├── types.ts              데이터 모양 정의 (팀 공용 약속)
│
├── api/
│   └── session.ts        데이터 가져오기 — 백엔드 연결 시 여기만 수정
├── data/
│   └── dummy.json        개발용 더미 분석 결과
├── constants/
│   └── emotions.ts       감정 색상, 신뢰도 기준값
│
└── components/
    ├── SummaryCards.tsx  요약 지표 4개
    ├── EmotionBand.tsx   발화별 대표 감정 색 띠
    ├── EmotionChart.tsx  감정 변화 곡선 + 감정 켜고 끄기
    ├── Transcript.tsx    전사본 목록
    ├── DetailPanel.tsx   발화 상세 패널 (화면 4)
    └── EmotionTag.tsx    감정 색 알약 태그 (공용)
```

## 상태가 흐르는 방식

`App.tsx`가 **선택된 발화 번호(`selected`) 하나**를 들고 있고,
곡선·색 띠·전사본·상세 패널은 모두 이 값만 바라봅니다.
그래서 어느 쪽을 클릭해도 나머지가 함께 반응합니다.

## 데이터

- 기술 스택: React 19 · TypeScript · Vite · Tailwind CSS 4 · Recharts
- `src/data/dummy.json`의 **문장**은 AI Hub「감성 대화 말뭉치」에서 추출했고,
  **감정 점수**는 모델이 준비되기 전까지 화면 개발을 위해 생성한 값입니다.
- 더미 데이터는 별도 파이썬 스크립트(`make_dummy.py`)로 생성합니다.
- 데이터 모양이 바뀌면 `src/types.ts`를 먼저 고치고 팀에 공유해 주세요.
