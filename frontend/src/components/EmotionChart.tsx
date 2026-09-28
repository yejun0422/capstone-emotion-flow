import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { Emotion, Utterance } from "../types";
import { EMOTION_COLORS } from "../constants/emotions";

interface Props {
  utterances: Utterance[];
  emotions: Emotion[];
  turningPoints: number[];
  selected: number | null;
  hidden: Emotion[];
  onSelect: (index: number) => void;
  onToggle: (emotion: Emotion) => void;
}

/** 감정 변화 곡선 + 감정 켜고 끄는 버튼 */
export default function EmotionChart({
  utterances,
  emotions,
  turningPoints,
  selected,
  hidden,
  onSelect,
  onToggle,
}: Props) {
  // Recharts가 원하는 평평한 모양으로 변환: { index, 불안, 분노, ... }
  const chartData = utterances.map((u) => ({
    index: u.index,
    ...u.scores,
  }));

  return (
    <section>
      <h2 className="mb-2 text-xs text-slate-500">
        감정 변화 곡선
        <span className="ml-2 text-slate-400">— 곡선이나 색 띠를 누르면 해당 발화로 이동합니다</span>
      </h2>

      <div className="cursor-pointer rounded-lg border border-slate-100 px-2 pt-4">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart
            data={chartData}
            onClick={(state) => {
              if (state.activeLabel !== undefined) {
                onSelect(Number(state.activeLabel));
              }
            }}
          >
            <CartesianGrid stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="index"
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              tickLine={false}
              axisLine={{ stroke: "#e2e8f0" }}
            />
            <YAxis
              domain={[0, 1]}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              tickLine={false}
              axisLine={false}
              width={32}
            />
            <Tooltip />
            {turningPoints.map((tp) => (
              <ReferenceLine key={tp} x={tp} stroke="#BA7517" strokeDasharray="4 4" />
            ))}
            {selected !== null && (
              <ReferenceLine x={selected} stroke="#1C1E21" strokeWidth={2} />
            )}
            {emotions.map((emo) => (
              <Line
                key={emo}
                type="monotone"
                dataKey={emo}
                stroke={EMOTION_COLORS[emo]}
                strokeWidth={2}
                dot={false}
                hide={hidden.includes(emo)}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 감정 필터 토글 */}
      <div className="mt-3 flex flex-wrap gap-2">
        {emotions.map((emo) => {
          const off = hidden.includes(emo);
          return (
            <button
              key={emo}
              onClick={() => onToggle(emo)}
              className={`flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs transition ${
                off
                  ? "border-slate-100 text-slate-300"
                  : "border-slate-300 text-slate-700 hover:bg-slate-50"
              }`}
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{ background: EMOTION_COLORS[emo], opacity: off ? 0.35 : 1 }}
              />
              {emo}
            </button>
          );
        })}
      </div>
    </section>
  );
}
