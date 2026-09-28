import type { ReactNode } from "react";
import type { Emotion } from "../types";
import { EMOTION_COLORS, EMOTION_TEXT } from "../constants/emotions";

interface Props {
  emotion: Emotion;
  children: ReactNode;
  size?: "sm" | "md";
}

/** 감정 색을 입힌 작은 알약 모양 태그 */
export default function EmotionTag({ emotion, children, size = "sm" }: Props) {
  return (
    <span
      className={`inline-block shrink-0 rounded-md font-medium ${
        size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs"
      }`}
      style={{
        background: `${EMOTION_COLORS[emotion]}1F`,
        color: EMOTION_TEXT[emotion],
      }}
    >
      {children}
    </span>
  );
}
