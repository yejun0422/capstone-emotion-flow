import { BrowserRouter, Routes, Route } from "react-router";
import AuthProvider from "./auth/AuthProvider";
import RequireAuth from "./auth/RequireAuth";
import LoginPage from "./pages/LoginPage";
import UploadPage from "./pages/UploadPage";
import SessionPage from "./pages/SessionPage";
import SessionListPage from "./pages/SessionListPage";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          {/* 이 안의 화면은 로그인해야 볼 수 있다 */}
          <Route element={<RequireAuth />}>
            <Route path="/" element={<UploadPage />} />
            <Route path="/sessions" element={<SessionListPage />} />
            <Route path="/sessions/:id" element={<SessionPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
