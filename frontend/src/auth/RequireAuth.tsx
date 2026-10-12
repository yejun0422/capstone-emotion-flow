import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "./AuthContext";

/** 로그인해야 볼 수 있는 화면들을 감싼다. 로그인 안 했으면 로그인 화면으로 보낸다. */
export default function RequireAuth() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) return null;   // 확인 중에는 아무것도 그리지 않는다 (깜빡임 방지)

  if (!user) {
    // 로그인 후 원래 가려던 곳으로 돌아오도록 주소를 같이 넘긴다
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
