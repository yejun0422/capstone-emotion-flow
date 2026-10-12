import type { Session, SessionListItem, SessionProgress } from "../types";

/** 파일을 올려 분석을 시작한다. 세션 ID를 즉시 돌려받는다. */
export async function uploadFile(
  file: File,
  counselor?: string,
): Promise<SessionProgress> {
  const form = new FormData();
  form.append("file", file);
  if (counselor) form.append("counselor", counselor);

  const res = await fetch("/api/sessions", { method: "POST", body: form });
  await check(res);
  return res.json();
}

/** 분석 진행률을 확인한다. */
export async function getProgress(id: string): Promise<SessionProgress> {
  const res = await fetch(`/api/sessions/${id}/status`);
  await check(res);
  return res.json();
}

/** 분석 결과 전체를 가져온다. */
export async function getSession(id: string): Promise<Session> {
  const res = await fetch(`/api/sessions/${id}`);
  await check(res);
  return res.json();
}

/** 저장된 분석 목록을 최신순으로 가져온다. */
export async function listSessions(): Promise<SessionListItem[]> {
  const res = await fetch("/api/sessions");
  await check(res);
  return res.json();
}

/** 분석 결과를 삭제한다. */
export async function deleteSession(id: string): Promise<void> {
  const res = await fetch(`/api/sessions/${id}`, { method: "DELETE" });
  await check(res);
}

/** 실패한 응답이면 에러를 던진다. 로그인이 풀렸으면(401) 로그인 화면으로 보낸다. */
async function check(res: Response): Promise<void> {
  if (res.ok) return;
  if (res.status === 401) window.location.assign("/login");
  throw new Error(await readError(res));
}

/** 서버가 보낸 에러 메시지를 꺼낸다. */
export async function readError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return "입력 형식이 올바르지 않습니다.";
  } catch {
    // 본문이 JSON이 아니면 아래 기본 문구
  }
  return `요청에 실패했습니다 (${res.status})`;
}
