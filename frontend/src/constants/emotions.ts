import type { Emotion } from "../types";

// 선·색 띠·막대에 쓰는 진한 색
// 비슷한 계열(불안·분노·상처)이 겹치지 않도록 색상환에서 고르게 떨어뜨린 값
export const EMOTION_COLORS: Record<Emotion, string> = {
  불안: "#9333EA",
  분노: "#E34948",
  상처: "#0891B2",
  슬픔: "#1F4E9C",
  당황: "#EDA100",
  기쁨: "#448A00",
};

// 태그 글자에 쓰는 더 진한 색 (밝은 배경 위에서 잘 읽히도록)
export const EMOTION_TEXT: Record<Emotion, string> = {
  불안: "#7A26C4",
  분노: "#B13938",
  상처: "#066E87",
  슬픔: "#1B4389",
  당황: "#895D00",
  기쁨: "#387100",
};

// 감정이 없는 발화에 쓰는 회색
export const GRAY = "#D3D1C7";

// 1등 점수가 이 값보다 낮으면 한 감정이 뚜렷하지 않은 "복합" 발화로 보고 1·2등을 함께 표시
// (backend/app/services/postprocess.py의 MIXED_THRESHOLD와 같은 값이어야 함)
	export const MIXED_THRESHOLD = 0.7;

// 점수(0~1)를 정수 퍼센트로 표시. 소수점 아래는 버림 (0.4175 → "41%", 0.006 → "0%")
// 1e-6은 0.29 × 100 = 28.999…처럼 컴퓨터 계산 오차로 1%가 깎이는 것을 막기 위한 값
export function toPercent(score: number): string {
  return `${Math.floor(score * 100 + 1e-6)}%`;
}
