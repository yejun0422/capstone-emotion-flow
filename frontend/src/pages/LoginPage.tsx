import { useState, type FormEvent } from "react";
import { Navigate, useLocation } from "react-router";
import { login, signup } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

const USERNAME_RULE = /^[A-Za-z0-9_]{3,30}$/;

/** 로그인 · 회원가입 화면 (한 화면에서 전환) */
export default function LoginPage() {
  const { user, loading, setUser } = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (loading) return null;
  if (user) return <Navigate to={from} replace />;   // 로그인되면 원래 가려던 곳으로

  const isSignup = mode === "signup";

  function switchMode() {
    setMode(isSignup ? "login" : "signup");
    setError(null);
    setPassword("");
    setConfirm("");
  }

  /** 회원가입 입력 검사 — 서버와 같은 규칙. 문제없으면 null */
  function validate(): string | null {
    if (!USERNAME_RULE.test(username)) return "아이디는 영문·숫자·밑줄(_)로 3~30자여야 합니다.";
    if (password.length < 8) return "비밀번호는 8자 이상이어야 합니다.";
    if (password.length > 128) return "비밀번호는 128자 이하여야 합니다.";
    if (password !== confirm) return "비밀번호 확인이 일치하지 않습니다.";
    return null;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();   // 폼 기본 동작(페이지 새로고침) 막기
    setError(null);

    if (isSignup) {
      const problem = validate();
      if (problem) {
        setError(problem);
        return;
      }
    }

    setBusy(true);
    try {
      const u = isSignup ? await signup(username, password) : await login(username, password);
      setUser(u);   // 위의 <Navigate>가 원래 가려던 곳으로 보낸다
    } catch (e) {
      setError(e instanceof Error ? e.message : "요청에 실패했습니다.");
      setBusy(false);
    }
  }

  const inputClass =
    "w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500";

  return (
    <div className="min-h-screen bg-slate-100 px-4 py-16">
      <div className="mx-auto max-w-sm overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <header className="border-b border-slate-100 px-5 py-3">
          <h1 className="text-sm font-semibold text-slate-900">감정 흐름 분석</h1>
        </header>

        <form onSubmit={handleSubmit} className="space-y-4 p-5">
          <h2 className="text-base font-semibold text-slate-900">
            {isSignup ? "회원가입" : "로그인"}
          </h2>

          <label className="block">
            <span className="mb-1 block text-xs text-slate-500">아이디</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
              className={inputClass}
            />
          </label>

          <label className="block">
            <span className="mb-1 block text-xs text-slate-500">비밀번호</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={isSignup ? "new-password" : "current-password"}
              required
              className={inputClass}
            />
          </label>

          {isSignup && (
            <label className="block">
              <span className="mb-1 block text-xs text-slate-500">비밀번호 확인</span>
              <input
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                autoComplete="new-password"
                required
                className={inputClass}
              />
            </label>
          )}

          {isSignup && (
            <p className="text-xs leading-relaxed text-slate-400">
              아이디는 영문·숫자·밑줄 3~30자, 비밀번호는 8자 이상입니다.
            </p>
          )}

          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-md bg-slate-900 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60"
          >
            {busy ? "처리 중…" : isSignup ? "가입하기" : "로그인"}
          </button>

          <p className="text-center text-xs text-slate-500">
            {isSignup ? "이미 계정이 있나요?" : "계정이 없나요?"}{" "}
            <button type="button" onClick={switchMode} className="text-slate-700 underline">
              {isSignup ? "로그인" : "회원가입"}
            </button>
          </p>
        </form>
      </div>
    </div>
  );
}
