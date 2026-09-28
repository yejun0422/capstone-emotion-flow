import { useEffect, useState } from "react";
import type { Emotion, Session } from "./types";
import { getSession } from "./api/session";
import SummaryCards from "./components/SummaryCards";
import EmotionBand from "./components/EmotionBand";
import EmotionChart from "./components/EmotionChart";
import Transcript from "./components/Transcript";
import DetailPanel from "./components/DetailPanel";

/** 화면 3: 분석 결과 대시보드 */
function App() {
  // ── 상태 ──────────────────────────────────────────
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<number | null>(null); // 선택된 발화 번호
  const [hidden, setHidden] = useState<Emotion[]>([]); // 곡선에서 숨긴 감정

  // 분석 결과 불러오기
  useEffect(() => {
    getSession()
      .then(setSession)
      .catch(() => setError("분석 결과를 불러오지 못했습니다."));
  }, []);

  // Esc 키로 상세 패널 닫기
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setSelected(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // ── 동작 ──────────────────────────────────────────
  function selectAndScroll(index: number) {
    setSelected(index);
    document
      .getElementById(`u-${index}`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function toggleEmotion(emo: Emotion) {
    setHidden((prev) =>
      prev.includes(emo) ? prev.filter((e) => e !== emo) : [...prev, emo],
    );
  }

  // ── 불러오는 중 / 실패 ─────────────────────────────
  if (error) {
    return <p className="p-10 text-center text-sm text-red-600">{error}</p>;
  }
  if (!session) {
    return <p className="p-10 text-center text-sm text-slate-400">불러오는 중…</p>;
  }

  // ── 화면에 쓸 값 계산 ──────────────────────────────
  const clientUtterances = session.utterances.filter((u) => u.speaker === "내담자");

  // 상세 패널용: 선택된 발화와 앞뒤 2개씩
  const pos = session.utterances.findIndex((u) => u.index === selected);
  const selectedUtterance = pos === -1 ? null : session.utterances[pos];
  const context = pos === -1 ? [] : session.utterances.slice(Math.max(0, pos - 2), pos + 3);

  // ── 화면 ──────────────────────────────────────────
  return (
    <>
      <div
        className={`min-h-screen bg-slate-100 px-4 py-10 transition-[padding] duration-300 ${
          selected !== null ? "lg:pr-[400px]" : ""
        }`}
      >
        <div className="mx-auto max-w-4xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <header className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
            <div className="flex items-baseline gap-2">
              <h1 className="text-sm font-semibold text-slate-900">{session.fileName}</h1>
              <span className="text-xs text-slate-400">
                발화 {session.utterances.length} · 화자 {session.speakers.length}
              </span>
            </div>
            <button className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-50">
              리포트
            </button>
          </header>

          <main className="space-y-7 p-5">
            <SummaryCards
              summary={session.summary}
              turningCount={session.turningPoints.length}
            />
            <EmotionBand
              utterances={clientUtterances}
              selected={selected}
              onSelect={selectAndScroll}
            />
            <EmotionChart
              utterances={clientUtterances}
              emotions={session.emotions}
              turningPoints={session.turningPoints}
              selected={selected}
              hidden={hidden}
              onSelect={selectAndScroll}
              onToggle={toggleEmotion}
            />
            <Transcript
              utterances={session.utterances}
              turningPoints={session.turningPoints}
              selected={selected}
              onSelect={setSelected}
            />
          </main>
        </div>
      </div>

      <DetailPanel
        utterance={selectedUtterance}
        context={context}
        isTurning={selected !== null && session.turningPoints.includes(selected)}
        onClose={() => setSelected(null)}
        onSelect={selectAndScroll}
      />
    </>
  );
}

export default App;
