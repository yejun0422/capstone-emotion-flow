import { NONVERBAL_RE } from "../constants/nonverbal";

interface Props {
  text: string;
}

/** 발화 원문을 그리되, 괄호류 비언어 정보는 회색으로 흐리게 표시한다. */
export default function UtteranceText({ text }: Props) {
  const parts: { text: string; nonverbal: boolean }[] = [];
  let last = 0;

  for (const m of text.matchAll(NONVERBAL_RE)) {
    const start = m.index ?? 0;
    if (start > last) parts.push({ text: text.slice(last, start), nonverbal: false });
    parts.push({ text: m[0], nonverbal: true });
    last = start + m[0].length;
  }
  if (last < text.length) parts.push({ text: text.slice(last), nonverbal: false });

  return (
    <>
      {parts.map((p, i) =>
        p.nonverbal ? (
          <span key={i} className="rounded bg-slate-100 px-0.5 text-[0.92em] text-slate-400">
            {p.text}
          </span>
        ) : (
          <span key={i}>{p.text}</span>
        ),
      )}
    </>
  );
}
