import type { Session } from "../types";

const SESSION_ID = "demo-001";

/**
 * 분석 결과를 서버에서 가져온다.
 *
 * 개발 중에는 Vite 프록시가 /api 요청을 localhost:8000으로 넘겨준다.
 */
export async function getSession(id: string = SESSION_ID): Promise<Session> {
  const res = await fetch(`/api/sessions/${id}`);

  if (!res.ok) {
    throw new Error(`분석 결과를 불러오지 못했습니다 (${res.status})`);
  }

  return res.json();
}
