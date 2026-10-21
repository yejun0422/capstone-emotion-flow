import { useState } from "react";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { Emotion, Utterance } from "../types";
import { EMOTION_COLORS, toPercent } from "../constants/emotions";

interface Props {
  utterances: Utterance[];
  emotions: Emotion[];
  turningPoints: number[];
  selected: number | null;
  hidden: Emotion[];
  onSelect: (index: number) => void;
  onToggle: (emotion: Emotion) => void;
}

type View = "line" | "mix";

// 구성비 그래프에서 아래부터 쌓는 순서
// 모델이 자주 헷갈리는 쌍(불안↔당황, 슬픔↔상처)을 서로 붙여 둔다
const STACK_ORDER: Emotion[] = ["불안", "당황", "분노", "슬픔", "상처", "기쁨"];

const VIEWS: { key: View; label: string }[] = [
  { key: "line", label: "감정별 선" },
  { key: "mix", label: "구성비" },
];

/** 감정 변화 그래프 (감정별 선 / 구성비 전환) + 감정 켜고 끄는 버튼 */
export default function EmotionChart({
  utterances,
  emotions,
  turningPoints,
  selected,
  hidden,
  onSelect,
  onToggle,
}: Props) {
  const [view, setView] = useState<View>("line");

  // Recharts가 원하는 평평한 모양으로 변환: { index, 불안, 분노, ... }
  // 점수가 없는 발화(판단 보류)는 빼서, 두 그래프 모두 선과 면이 끊기지 않고 이어지게 한다
  const chartData = utterances
    .filter((u) => u.scores !== null)
    .map((u) => ({
      index: u.index,
      ...u.scores,
    }));

  // 두 그래프가 함께 쓰는 격자·축·툴팁
  const common = [
    <CartesianGrid key="grid" stroke="#f1f5f9" vertical={false} />,
    <XAxis
      key="x"
      dataKey="index"
      tick={{ fontSize: 11, fill: "#94a3b8" }}
      tickLine={false}
      axisLine={{ stroke: "#e2e8f0" }}
    />,
    <YAxis
      key="y"
      domain={[0, 1]}
      allowDataOverflow
      tickFormatter={(v: number) => toPercent(v)}
      tick={{ fontSize: 11, fill: "#94a3b8" }}
      tickLine={false}
      axisLine={false}
      width={40}
    />,
    <Tooltip key="tooltip" formatter={(v) => toPercent(Number(v))} />,
  ];

  // 전환점 점선과 선택한 발화 표시
  const markers = [
    ...turningPoints.map((tp) => (
      <ReferenceLine
        key={`tp-${tp}`}
        x={tp}
        // 흰 배경(감정별 선)에서는 검정, 색 면(구성비) 위에서는 흰색 점선
        stroke={view === "line" ? "#1C1E21" : "#FFFFFF"}
        strokeWidth={view === "line" ? 1.5 : 2}
        strokeDasharray="5 4"
      />
    )),
    selected !== null && (
      <ReferenceLine key="selected" x={selected} stroke="#1C1E21" strokeWidth={2} />
    ),
  ];

  function handleClick(state: { activeLabel?: string | number }) {
    if (state.activeLabel !== undefined) {
      onSelect(Number(state.activeLabel));
    }
  }

  return (
    <section>
      <div className="mb-2 flex items-center justify-between gap-2">
        <h2 className="text-xs text-slate-500">
          감정 변화 그래프
          <span className="ml-2 text-slate-400">— 그래프나 색 띠를 누르면 해당 발화로 이동합니다</span>
        </h2>

        {/* 그래프 방식 전환 */}
        <div className="flex shrink-0 rounded-md border border-slate-200 p-0.5 text-xs">
          {VIEWS.map((v) => (
            <button
              key={v.key}
              onClick={() => setView(v.key)}
              className={`rounded px-2.5 py-1 transition ${
                view === v.key ? "bg-slate-800 text-white" : "text-slate-500 hover:bg-slate-50"
              }`}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>

      <div className="cursor-pointer rounded-lg border border-slate-100 px-2 pt-4">
        <ResponsiveContainer width="100%" height={260}>
          {view === "line" ? (
            <LineChart data={chartData} onClick={handleClick}>
              {common}
              {markers}
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
          ) : (
            <AreaChart data={chartData} onClick={handleClick}>
              {common}
              {STACK_ORDER.map((emo) => (
                <Area
                  key={emo}
                  type="monotone"
                  dataKey={emo}
                  stackId="mix"
                  // 툴팁 글자색은 stroke를 따라가므로, 테두리 없이 fill 색이 쓰이게 한다
                  stroke="none"
                  fill={EMOTION_COLORS[emo]}
                  fillOpacity={1}
                  hide={hidden.includes(emo)}
                />
              ))}
              {markers}
            </AreaChart>
          )}
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
