import type { Utterance } from "../types";
import { EMOTION_COLORS, GRAY } from "../constants/emotions";

interface Props {
  utterances: Utterance[];
  selected: number | null;
  onSelect: (index: number) => void;
}

/** 발화별 대표 감정을 색으로 이어 붙인 가로 띠 */
export default function EmotionBand({ utterances, selected, onSelect }: Props) {
  return (
    <section>
      <h2 className="mb-2 text-xs text-slate-500">발화별 대표 감정</h2>
      <div className="flex h-3.5 overflow-hidden rounded">
        {utterances.map((u) => (
          <div
            key={u.index}
            title={`${u.index}번 · ${u.top ?? "판단 보류"}`}
            onClick={() => onSelect(u.index)}
            className="flex-1 cursor-pointer"
            style={{
              background: u.top === null ? GRAY : EMOTION_COLORS[u.top],
              outline: selected === u.index ? "2px solid #1C1E21" : "none",
              outlineOffset: -2,
            }}
          />
        ))}
      </div>
    </section>
  );
}
