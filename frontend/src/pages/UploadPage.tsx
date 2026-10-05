import { useState } from "react";
import { useNavigate } from "react-router";
import { uploadFile } from "../api/session";

export default function UploadPage() {
  const navigate = useNavigate();
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleFile(file: File) {
    setError(null);
    setBusy(true);
    try {
      const { sessionId } = await uploadFile(file);
      navigate(`/sessions/${sessionId}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "업로드에 실패했습니다.");
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 px-4 py-10">
      <div className="mx-auto max-w-2xl overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <header className="border-b border-slate-100 px-5 py-3">
          <h1 className="text-sm font-semibold text-slate-900">감정 흐름 분석</h1>
        </header>

        <main className="p-5">
          <label
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              const file = e.dataTransfer.files[0];
              if (file) handleFile(file);
            }}
            className={`flex cursor-pointer flex-col items-center rounded-xl border border-dashed px-4 py-12 text-center transition ${
              dragging ? "border-slate-500 bg-slate-100" : "border-slate-300 bg-slate-50"
            } ${busy ? "pointer-events-none opacity-60" : ""}`}
          >
            <input
              type="file"
              accept=".txt,.csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
            <p className="text-base font-semibold text-slate-900">
              {busy ? "업로드 중…" : "대화 기록 파일을 여기에 놓으세요"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              상담 축어록 (.txt) · CSV · 카카오톡 내보내기 (.txt)
            </p>
            <span className="mt-4 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700">
              파일 선택
            </span>
          </label>

          {error && (
            <p className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
          )}

          <div className="mt-6 rounded-lg bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-500">
            업로드한 파일은 서버에 저장되지 않으며, 분석 후 즉시 폐기됩니다.
            이름·전화번호·이메일 등은 자동으로 가려집니다.
          </div>
        </main>
      </div>
    </div>
  );
}
