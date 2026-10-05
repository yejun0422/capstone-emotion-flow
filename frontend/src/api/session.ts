import type { Session, SessionProgress } from "../types";

/** 파일을 올려 분석을 시작한다. 세션 ID를 즉시 돌려받는다. */
export async function uploadFile(
  file: File,
  counselor?: string,
): Promise<SessionProgress> {
  const form = new FormData();
  form.append("file", file);
  if (counselor) form.append("counselor", counselor);

  const res = await fetch("/api/sessions", { method: "POST", body: form });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

/** 분석 진행률을 확인한다. */
export async function getProgress(id: string): Promise<SessionProgress> {
  const res = await fetch(`/api/sessions/${id}/status`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

/** 분석 결과 전체를 가져온다. */
export async function getSession(id: string): Promise<Session> {
  const res = await fetch(`/api/sessions/${id}`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

/** 서버가 보낸 에러 메시지를 꺼낸다. */
async function readError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body.detail ?? `요청에 실패했습니다 (${res.status})`;
  } catch {
    return `요청에 실패했습니다 (${res.status})`;
  }
}
