import type { Utterance } from "../types";
import { LOW_CONFIDENCE } from "../constants/emotions";
import EmotionTag from "./EmotionTag";

interface Props {
  utterances: Utterance[];
  turningPoints: number[];
  selected: number | null;
  onSelect: (index: number | null) => void;
}

/** 전사본 목록 */
export default function Transcript({ utterances, turningPoints, selected, onSelect }: Props) {
  const turningSet = new Set(turningPoints);

  return (
    <section>
      <h2 className="mb-2 text-xs text-slate-500">
        전사본
        <span className="ml-2 text-slate-400">— 발화를 누르면 상세 정보가 열립니다</span>
      </h2>
      <div className="divide-y divide-slate-100 rounded-lg border border-slate-100">
        {utterances.map((u) => {
          const isSelected = selected === u.index;
          const isTurning = turningSet.has(u.index);
          const weak = u.confidence !== null && u.confidence < LOW_CONFIDENCE;

          return (
            <div
              key={u.index}
              id={`u-${u.index}`}
              onClick={() => onSelect(isSelected ? null : u.index)}
              className={`flex cursor-pointer items-baseline gap-3 border-l-2 px-3 py-2.5 transition-colors ${
                isTurning ? "border-l-amber-500" : "border-l-transparent"
              } ${isSelected ? "bg-amber-50" : "hover:bg-slate-50"}`}
              style={{ opacity: weak ? 0.5 : 1 }}
            >
              <span className="w-7 shrink-0 text-xs tabular-nums text-slate-400">{u.index}</span>
              <span className="w-10 shrink-0 text-xs text-slate-400">{u.speaker}</span>
              <span className="flex-1 text-sm leading-relaxed text-slate-800">{u.text}</span>

              {u.top === null || u.confidence === null ? (
                <span className="shrink-0 rounded-md border border-dashed border-slate-300 px-2 py-0.5 text-[11px] text-slate-400">
                  판단 보류
                </span>
              ) : (
                <EmotionTag emotion={u.top}>
                  {u.top} {u.confidence.toFixed(2)}
                </EmotionTag>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
