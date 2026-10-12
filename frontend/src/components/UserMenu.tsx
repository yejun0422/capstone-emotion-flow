import { useNavigate } from "react-router";
import { logout } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

/** 헤더 오른쪽: 로그인한 아이디와 로그아웃 버튼 */
export default function UserMenu() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // 서버 오류가 나도 화면에서는 로그아웃 처리한다
    }
    setUser(null);
    navigate("/login", { replace: true });
  }

  if (!user) return null;

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-slate-400">{user.username}</span>
      <button
        onClick={handleLogout}
        className="rounded-md px-2 py-1 text-xs text-slate-400 hover:bg-slate-50 hover:text-slate-600"
      >
        로그아웃
      </button>
    </div>
  );
}
