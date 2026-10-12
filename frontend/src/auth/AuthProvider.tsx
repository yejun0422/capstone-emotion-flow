import { useEffect, useState, type ReactNode } from "react";
import type { User } from "../types";
import { getMe } from "../api/auth";
import { AuthContext } from "./AuthContext";

/** 앱 전체를 감싸서, 처음 열 때 로그인 여부를 한 번 확인하고 모든 화면에 나눠준다. */
export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  return <AuthContext value={{ user, loading, setUser }}>{children}</AuthContext>;
}
