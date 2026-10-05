import { useEffect, useState } from "react";
import { useParams } from "react-router";
import type { Session } from "../types";
import { getProgress, getSession } from "../api/session";
import Dashboard from "../components/Dashboard";
import Progress from "../components/Progress";

const POLL_INTERVAL = 1000;

export default function SessionPage() {
  const { id = "" } = useParams();

  const [session, setSession] = useState<Session | null>(null);
  const [done, setDone] = useState(0);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    let timer: number;

    async function poll() {
      try {
        const p = await getProgress(id);
        if (!alive) return;

        setDone(p.done);
        setTotal(p.total);

        if (p.status === "done") {
          setSession(await getSession(id));
        } else if (p.status === "failed") {
          // 실패하면 서버가 사유를 오류 응답으로 보낸다 → 아래 catch에서 화면에 표시
          await getSession(id);
        } else {
          timer = window.setTimeout(poll, POLL_INTERVAL);
        }
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : "불러오지 못했습니다.");
      }
    }

    poll();
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
  }, [id]);

  if (error) {
    return (
      <div className="min-h-screen bg-slate-100 px-4 py-10">
        <p className="mx-auto max-w-2xl rounded-xl bg-red-50 px-5 py-4 text-sm text-red-700">
          {error}
        </p>
      </div>
    );
  }

  if (!session) return <Progress done={done} total={total} />;

  return <Dashboard data={session} />;
}
