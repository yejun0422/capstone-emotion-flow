import type { Summary } from "../types";

interface Props {
  summary: Summary;
  turningCount: number;
}

/** 화면 상단의 요약 지표 4개 */
export default function SummaryCards({ summary, turningCount }: Props) {
  const metrics = [
    { label: "대표 감정", value: summary.dominant },
    { label: "전환점", value: `${turningCount}회` },
    { label: "감정 변동성", value: summary.volatility },
    { label: "낮은 신뢰도", value: `${Math.round(summary.lowConfidenceRatio * 100)}%` },
  ];

  return (
    <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {metrics.map((m) => (
        <div key={m.label} className="rounded-lg bg-slate-50 px-4 py-3">
          <div className="text-xs text-slate-500">{m.label}</div>
          <div className="mt-1 text-xl font-semibold text-slate-900">{m.value}</div>
        </div>
      ))}
    </section>
  );
}
