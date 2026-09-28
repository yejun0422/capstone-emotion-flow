import type { Emotion, Utterance } from "../types";
import { EMOTION_COLORS, LOW_CONFIDENCE } from "../constants/emotions";
import EmotionTag from "./EmotionTag";

interface Props {
  utterance: Utterance | null;
  context: Utterance[];
  isTurning: boolean;
  onClose: () => void;
  onSelect: (index: number) => void;
}

/** 오른쪽에서 밀려 나오는 발화 상세 패널 (화면 4) */
export default function DetailPanel({ utterance, context, isTurning, onClose, onSelect }: Props) {
  const open = utterance !== null;

  // 점수 높은 순으로 정렬
  const bars = utterance?.scores
    ? (Object.entries(utterance.scores) as [Emotion, number][]).sort((a, b) => b[1] - a[1])
    : [];

  const weak = utterance?.confidence != null && utterance.confidence < LOW_CONFIDENCE;

  return (
    <aside
      className={`fixed inset-y-0 right-0 z-20 flex w-full max-w-sm flex-col border-l border-slate-200 bg-white shadow-xl transition-transform duration-300 ${
        open ? "translate-x-0" : "translate-x-full"
      }`}
      aria-hidden={!open}
    >
      {utterance && (
        <>
          {/* 헤더 */}
          <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
            <span className="text-sm font-semibold text-slate-900">
              발화 {utterance.index} · {utterance.speaker}
            </span>
            <button
              onClick={onClose}
              className="rounded-md px-2 py-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              aria-label="닫기"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 space-y-6 overflow-y-auto px-5 py-5">
            {/* 문맥 */}
            <section>
              <h3 className="mb-2 text-xs text-slate-500">문맥</h3>
              <div className="space-y-1.5 border-l-2 border-slate-200 pl-3">
                {context.map((c) => {
                  const current = c.index === utterance.index;
                  return (
                    <button
                      key={c.index}
                      onClick={() => onSelect(c.index)}
                      disabled={current}
                      className={`block w-full text-left text-sm leading-relaxed ${
                        current
                          ? "font-semibold text-slate-900"
                          : "text-slate-400 hover:text-slate-700"
                      }`}
                    >
                      <span className="mr-1.5 text-xs tabular-nums">{c.index}</span>
                      <span className="mr-1.5 text-xs">{c.speaker}</span>
                      {c.text}
                    </button>
                  );
                })}
              </div>
            </section>

            {utterance.scores === null ? (
              <p className="rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-500">
                상담자 발화는 감정 분석 대상이 아닙니다.
              </p>
            ) : (
              <>
                {/* 감정 분포 */}
                <section>
                  <h3 className="mb-2 text-xs text-slate-500">감정 분포 (대분류)</h3>
                  <div className="space-y-2">
                    {bars.map(([emo, score]) => {
                      const low = score < 0.2;
                      return (
                        <div key={emo} className="flex items-center gap-2">
                          <span className={`w-9 text-xs ${low ? "text-slate-400" : "text-slate-700"}`}>
                            {emo}
                          </span>
                          <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full"
                              style={{ width: `${score * 100}%`, background: EMOTION_COLORS[emo] }}
                            />
                          </div>
                          <span
                            className={`w-9 text-right text-xs tabular-nums ${
                              low ? "text-slate-400" : "text-slate-600"
                            }`}
                          >
                            {score.toFixed(2)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </section>

                {/* 세부 감정 */}
                <section>
                  <h3 className="mb-2 text-xs text-slate-500">세부 감정 (소분류)</h3>
                  {utterance.top && utterance.topSub ? (
                    <EmotionTag emotion={utterance.top} size="md">
                      {utterance.topSub}
                    </EmotionTag>
                  ) : (
                    <p className="text-xs text-slate-400">세부 감정을 판단하기 어렵습니다.</p>
                  )}
                </section>

                {/* 안내 */}
                {isTurning && (
                  <div className="rounded-lg bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-900">
                    이 발화는 전환점으로 탐지되었습니다. 직전 구간과 대표 감정이 달라집니다.
                  </div>
                )}
                {weak && (
                  <div className="rounded-lg bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-600">
                    확신이 낮은 추론입니다. 위 문맥과 함께 판단해 주세요.
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}
    </aside>
  );
}
