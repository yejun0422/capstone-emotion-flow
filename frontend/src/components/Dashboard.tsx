import { useEffect, useState } from "react";
import { Link } from "react-router";
import type { Emotion, Session } from "../types";
import SummaryCards from "./SummaryCards";
import EmotionBand from "./EmotionBand";
import EmotionChart from "./EmotionChart";
import Transcript from "./Transcript";
import DetailPanel from "./DetailPanel";

interface Props {
  data: Session;
}

/** 화면 3: 분석 결과 대시보드 */
export default function Dashboard({ data }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const [hidden, setHidden] = useState<Emotion[]>([]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setSelected(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

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

  const clientUtterances = data.utterances.filter((u) => u.speaker === "내담자");

  const pos = data.utterances.findIndex((u) => u.index === selected);
  const selectedUtterance = pos === -1 ? null : data.utterances[pos];
  const context = pos === -1 ? [] : data.utterances.slice(Math.max(0, pos - 2), pos + 3);

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
              <h1 className="text-sm font-semibold text-slate-900">{data.fileName}</h1>
              <span className="text-xs text-slate-400">
                발화 {data.utterances.length} · 화자 {data.speakers.length}
              </span>
            </div>
            <div className="flex gap-2">
              <Link
                to="/sessions"
                className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-50"
              >
                목록
              </Link>
              <Link
                to="/"
                className="rounded-md border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-50"
              >
                새 분석
              </Link>
            </div>
          </header>

          <main className="space-y-7 p-5">
            <SummaryCards
              summary={data.summary}
              turningCount={data.turningPoints.length}
            />
            <EmotionBand
              utterances={clientUtterances}
              selected={selected}
              onSelect={selectAndScroll}
            />
            <EmotionChart
              utterances={clientUtterances}
              emotions={data.emotions}
              turningPoints={data.turningPoints}
              selected={selected}
              hidden={hidden}
              onSelect={selectAndScroll}
              onToggle={toggleEmotion}
            />
            <Transcript
              utterances={data.utterances}
              turningPoints={data.turningPoints}
              selected={selected}
              onSelect={setSelected}
            />
          </main>
        </div>
      </div>

      <DetailPanel
        utterance={selectedUtterance}
        context={context}
        isTurning={selected !== null && data.turningPoints.includes(selected)}
        onClose={() => setSelected(null)}
        onSelect={selectAndScroll}
      />
    </>
  );
}
