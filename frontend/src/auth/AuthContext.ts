import { createContext, useContext } from "react";
import type { User } from "../types";

interface AuthState {
  user: User | null;        // 로그인한 사용자, 없으면 null
  loading: boolean;         // 처음 로그인 여부를 확인하는 중인지
  setUser: (user: User | null) => void;
}

export const AuthContext = createContext<AuthState | null>(null);

/** 어느 화면에서든 로그인 정보를 꺼내 쓴다. */
export function useAuth(): AuthState {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth는 AuthProvider 안에서만 쓸 수 있습니다.");
  return value;
}
