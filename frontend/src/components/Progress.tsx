interface Props {
  done: number;
  total: number;
}

/** 분석 진행 화면 (화면 2) */
export default function Progress({ done, total }: Props) {
  const percent = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="min-h-screen bg-slate-100 px-4 py-10">
      <div className="mx-auto max-w-2xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-2 flex items-baseline justify-between">
          <span className="text-sm font-semibold text-slate-900">감정 분석 중</span>
          <span className="text-xs text-slate-500">
            {total > 0 ? `${total}개 중 ${done}개` : "파일을 읽는 중…"}
          </span>
        </div>

        <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-slate-700 transition-[width] duration-500"
            style={{ width: `${percent}%` }}
          />
        </div>

        <p className="mt-4 text-xs text-slate-400">
          발화 수에 따라 몇 초에서 1분 정도 걸립니다.
        </p>
      </div>
    </div>
  );
}
