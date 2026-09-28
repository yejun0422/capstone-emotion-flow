import type { Session } from "../types";
import dummy from "../data/dummy.json";

/**
 * 분석 결과를 가져온다.
 *
 * 지금은 더미 데이터를 그대로 돌려준다.
 * 백엔드가 생기면 이 함수 안만 서버 요청으로 바꾸면 되고,
 * 화면 코드는 건드릴 필요가 없다.
 *
 * 예시 (백엔드 연결 후):
 *   const res = await fetch(`/api/sessions/${id}`);
 *   return res.json();
 */
export async function getSession(): Promise<Session> {
  return dummy as Session;
}
