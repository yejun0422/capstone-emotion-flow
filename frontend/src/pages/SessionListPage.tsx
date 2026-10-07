import { useEffect, useState } from "react";
import { Link } from "react-router";
import type { Emotion, SessionListItem } from "../types";
import { deleteSession, listSessions } from "../api/session";
import { EMOTION_COLORS, GRAY } from "../constants/emotions";

const STATUS_LABEL = {
  processing: { text: "분석 중", className: "bg-slate-100 text-slate-500" },
  failed: { text: "실패", className: "bg-red-50 text-red-600" },
} as const;

/** 화면 5: 저장된 분석 목록 */
export default function SessionListPage() {
  const [items, setItems] = useState<SessionListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSessions()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "목록을 불러오지 못했습니다."));
  }, []);

  async function handleDelete(item: SessionListItem) {
    if (!window.confirm(`'${item.fileName}' 분석 결과를 삭제할까요?\n삭제하면 되돌릴 수 없습니다.`)) {
      return;
    }
    try {
      await deleteSession(item.sessionId);
      setItems((prev) => prev?.filter((x) => x.sessionId !== item.sessionId) ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "삭제하지 못했습니다.");
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 px-4 py-10">
      <div className="mx-auto max-w-3xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <header className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <div className="flex items-baseline gap-2">
            <h1 className="text-sm font-semibold text-slate-900">세션 목록</h1>
            {items && <span className="text-xs text-slate-400">{items.length}건</span>}
          </div>
          <Link
            to="/"
            className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-50"
          >
            새 분석
          </Link>
        </header>

        <main className="p-5">
          {error && (
            <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
          )}

          {items === null && !error && (
            <p className="py-10 text-center text-sm text-slate-400">불러오는 중…</p>
          )}

          {items?.length === 0 && (
            <div className="py-12 text-center">
              <p className="text-sm text-slate-500">아직 분석한 기록이 없습니다.</p>
              <Link to="/" className="mt-3 inline-block text-sm text-slate-700 underline">
                첫 축어록 올리기
              </Link>
            </div>
          )}

          {items && items.length > 0 && (
            <ul className="divide-y divide-slate-100 rounded-lg border border-slate-100">
              {items.map((item) => (
                <li key={item.sessionId} className="flex items-center gap-4 px-4 py-3 hover:bg-slate-50">
                  <Link to={`/sessions/${item.sessionId}`} className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate text-sm font-medium text-slate-900">
                        {item.fileName}
                      </span>
                      {item.status !== "done" && (
                        <span
                          className={`shrink-0 rounded px-1.5 py-0.5 text-[11px] ${STATUS_LABEL[item.status].className}`}
                        >
                          {STATUS_LABEL[item.status].text}
                        </span>
                      )}
                    </div>
                    <MiniBand tops={item.tops} />
                  </Link>

                  <div className="hidden shrink-0 text-right sm:block">
                    <div className="text-xs text-slate-500">
                      발화 {item.utteranceCount} · 전환점 {item.turningCount}
                    </div>
                    <div className="text-xs text-slate-400">{formatDate(item.createdAt)}</div>
                  </div>

                  <button
                    onClick={() => handleDelete(item)}
                    className="shrink-0 rounded-md px-2 py-1 text-xs text-slate-400 hover:bg-red-50 hover:text-red-600"
                    aria-label={`${item.fileName} 삭제`}
                  >
                    삭제
                  </button>
                </li>
              ))}
            </ul>
          )}
        </main>
      </div>
    </div>
  );
}

/** 내담자 발화별 대표 감정을 이어 붙인 작은 색 띠 */
function MiniBand({ tops }: { tops: (Emotion | null)[] }) {
  if (tops.length === 0) {
    return <div className="mt-1.5 h-2 max-w-xs rounded-sm bg-slate-100" />;
  }
  return (
    <div className="mt-1.5 flex h-2 max-w-xs overflow-hidden rounded-sm">
      {tops.map((top, i) => (
        <div
          key={i}
          className="flex-1"
          style={{ background: top === null ? GRAY : EMOTION_COLORS[top] }}
        />
      ))}
    </div>
  );
}

/** "2026-10-07T19:08:00" → "2026.10.07 19:08" */
function formatDate(iso: string): string {
  const d = new Date(iso);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}.${p(d.getMonth() + 1)}.${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
