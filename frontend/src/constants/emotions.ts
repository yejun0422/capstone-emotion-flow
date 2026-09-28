import type { Emotion } from "../types";

// 선·색 띠·막대에 쓰는 진한 색
export const EMOTION_COLORS: Record<Emotion, string> = {
  불안: "#D85A30",
  분노: "#E24B4A",
  상처: "#D4537E",
  슬픔: "#7F77DD",
  당황: "#EF9F27",
  기쁨: "#1D9E75",
};

// 태그 글자에 쓰는 더 진한 색 (밝은 배경 위에서 잘 읽히도록)
export const EMOTION_TEXT: Record<Emotion, string> = {
  불안: "#993C1D",
  분노: "#A32D2D",
  상처: "#993556",
  슬픔: "#3C3489",
  당황: "#854F0B",
  기쁨: "#0F6E56",
};

// 감정이 없는 발화에 쓰는 회색
export const GRAY = "#D3D1C7";

// 신뢰도가 이 값보다 낮으면 "확신 없는 추론"으로 흐리게 표시
export const LOW_CONFIDENCE = 0.5;
