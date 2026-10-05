# 감정 흐름 분석 — 프론트엔드

상담 축어록을 올리면 발화 순서에 따른 감정 변화를 곡선으로 보여주고,
감정이 크게 바뀐 지점(전환점)을 표시하는 웹 화면입니다.

2026-2학기 산학캡스톤디자인 · 팀 안성맞춤

---

## 실행 방법

Node.js 20 이상이 필요합니다. **백엔드 서버가 먼저 켜져 있어야** 합니다.
(백엔드 실행은 `backend/README.md` 참고)

```bash
npm install     # 처음 한 번만
npm run dev     # 개발 서버 실행 → http://localhost:5173
```

개발 중에는 Vite가 `/api`로 시작하는 요청을 `http://localhost:8000`(백엔드)으로 넘겨줍니다.
설정은 `vite.config.ts`의 `server.proxy`에 있습니다.

| 명령어 | 하는 일 |
|---|---|
| `npm run build` | 타입 검사 후 배포용 파일을 `dist/`에 생성 |
| `npm run lint` | 코드 검사 (Oxlint) |
| `npm run preview` | 빌드 결과를 로컬에서 미리 보기 |

---

## 화면과 주소

| 주소 | 파일 | 화면 |
|---|---|---|
| `/` | `pages/UploadPage.tsx` | 화면 1 — 업로드 |
| `/sessions/:id` | `pages/SessionPage.tsx` | 분석 중이면 화면 2(진행), 끝나면 화면 3·4(결과) |

`SessionPage`가 1초마다 진행률을 확인하다가, 분석이 끝나면 결과를 받아 대시보드를 보여줍니다.

---

## 폴더 구조

```
src/
├── main.tsx                앱 시작점 (건드릴 일 없음)
├── App.tsx                 주소별 화면 연결 (React Router)
├── index.css               Tailwind 불러오기
├── types.ts                데이터 모양 정의 — backend/app/schemas.py와 대응
│
├── pages/
│   ├── UploadPage.tsx      화면 1: 파일 업로드
│   └── SessionPage.tsx     화면 2·3: 진행률 확인 → 결과 표시
│
├── api/
│   └── session.ts          서버 요청 (업로드, 진행률, 결과 조회)
│
├── constants/
│   ├── emotions.ts         감정 색상, 신뢰도 기준값
│   └── nonverbal.ts        비언어 판별 규칙 — backend/app/services/text_rules.py와 대응
│
├── data/
│   └── dummy.json          데모 데이터 (백엔드 seed.py가 읽어 DB에 넣음)
│
└── components/
    ├── Progress.tsx        화면 2: 분석 진행률
    ├── Dashboard.tsx       화면 3: 결과 대시보드 조립 + 선택 상태 관리
    ├── SummaryCards.tsx    요약 지표 4개
    ├── EmotionBand.tsx     발화별 대표 감정 색 띠
    ├── EmotionChart.tsx    감정 변화 곡선 + 감정 켜고 끄기
    ├── Transcript.tsx      전사본 목록
    ├── DetailPanel.tsx     화면 4: 발화 상세 패널
    ├── UtteranceText.tsx   발화 원문 표시 (괄호류는 회색 처리)
    └── EmotionTag.tsx      감정 색 알약 태그 (공용)
```

---

## 상태가 흐르는 방식

`Dashboard.tsx`가 **선택된 발화 번호(`selected`) 하나**를 들고 있고,
곡선·색 띠·전사본·상세 패널은 모두 이 값만 바라봅니다.
그래서 어느 쪽을 클릭해도 나머지가 함께 반응합니다.

| 동작 | 반응 |
|---|---|
| 곡선 또는 색 띠 클릭 | 전사본이 해당 발화로 스크롤, 상세 패널 열림 |
| 전사본 발화 클릭 | 상세 패널 열림 (한 번 더 누르면 닫힘) |
| 감정 버튼 클릭 | 해당 감정 곡선 표시 · 숨김 |
| Esc | 상세 패널 닫기 |

---

## 화면 표시 규칙

- **괄호류(비언어 정보)** 는 원문 위치에 그대로 두되 회색으로 흐리게 표시합니다.
  `( )` `(( ))` `[ ]` `{ }` `*한숨*` 모두 같은 취급입니다. 분석에는 쓰이지 않습니다.
- 마스킹된 개인정보는 `〈이름〉` `〈전화번호〉` 처럼 보입니다.
- **신뢰도 0.5 미만** 발화는 흐리게 표시합니다.
- 상담자 발화와 분석 대상이 아닌 짧은 발화는 "판단 보류"로 표시합니다.
- 전환점 발화는 전사본 왼쪽에 주황 세로줄이 붙습니다.

---

## 같이 고쳐야 하는 파일

| 프론트 | 백엔드 | 내용 |
|---|---|---|
| `src/types.ts` | `app/schemas.py` | 데이터 모양 |
| `src/constants/nonverbal.ts` | `app/services/text_rules.py` | 비언어 판별 규칙 |

한쪽만 고치면 화면과 분석이 어긋납니다. 고친 뒤에는 팀에 공유해 주세요.

---

## 기술 스택

React 19 · TypeScript · Vite · Tailwind CSS 4 · Recharts · React Router

---

## 데이터

- 문장은 AI Hub「감성 대화 말뭉치」에서 추출했고, 감정 점수는 현재 백엔드의 임시 분석기가 만든 값입니다.
- 모델이 연결되면 프론트는 고칠 것이 없습니다. 서버가 보내는 점수만 바뀝니다.
