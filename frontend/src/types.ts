// 감정 6종 — 이 중 하나만 들어갈 수 있다
export type Emotion = "불안" | "분노" | "상처" | "슬픔" | "당황" | "기쁨";

// 화자 2종
export type Speaker = "상담자" | "내담자";

// 감정별 점수 — 6개 감정 각각에 숫자가 붙는다
export type EmotionScores = Record<Emotion, number>;

// 발화 하나
export interface Utterance {
  index: number;
  speaker: Speaker;
  text: string;
  scores: EmotionScores | null;   // 상담자 발화는 null
  top: Emotion | null;
  topSub: string | null;
  confidence: number | null;
}

// 요약 지표
export interface Summary {
  dominant: Emotion;
  volatility: number;
  lowConfidenceRatio: number;
}

// 분석 결과 전체
export interface Session {
  sessionId: string;
  fileName: string;
  speakers: Speaker[];
  emotions: Emotion[];
  utterances: Utterance[];
  turningPoints: number[];
  summary: Summary;
}