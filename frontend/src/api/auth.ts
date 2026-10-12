import type { User } from "../types";
import { readError } from "./session";

/** 회원가입. 성공하면 바로 로그인 상태가 된다. */
export async function signup(username: string, password: string): Promise<User> {
  const res = await fetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

/** 로그인. 성공하면 서버가 쿠키를 내려준다. */
export async function login(username: string, password: string): Promise<User> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

/** 로그아웃. */
export async function logout(): Promise<void> {
  const res = await fetch("/api/auth/logout", { method: "POST" });
  if (!res.ok) throw new Error(await readError(res));
}

/** 지금 로그인한 사용자. 로그인 안 돼 있으면 null. */
export async function getMe(): Promise<User | null> {
  const res = await fetch("/api/auth/me");
  if (res.status === 401) return null;
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}
