import { BrowserRouter, Routes, Route } from "react-router";
import UploadPage from "./pages/UploadPage";
import SessionPage from "./pages/SessionPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/sessions/:id" element={<SessionPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
