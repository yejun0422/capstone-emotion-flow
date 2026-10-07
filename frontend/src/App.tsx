import { BrowserRouter, Routes, Route } from "react-router";
import UploadPage from "./pages/UploadPage";
import SessionPage from "./pages/SessionPage";
import SessionListPage from "./pages/SessionListPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/sessions" element={<SessionListPage />} />
        <Route path="/sessions/:id" element={<SessionPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
