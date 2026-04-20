import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { fetchQuiz } from "../api/client";
import type { Level } from "../api/types";
import { levelLabel, useSessionStore } from "../store/session";

const LEVELS = new Set<Level>(["easy", "medium", "hard"]);

export default function StartPage() {
  const { level: raw } = useParams();
  const navigate = useNavigate();
  const setQuiz = useSessionStore((s) => s.setQuiz);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const level = useMemo(() => {
    if (!raw || !LEVELS.has(raw as Level)) return null;
    return raw as Level;
  }, [raw]);

  if (!level) {
    return (
      <div className="app-shell">
        <p>无效的等级</p>
        <Link to="/">回到首页</Link>
      </div>
    );
  }

  const onStart = async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await fetchQuiz(level, 10);
      setQuiz(data.level, data.questions);
      navigate(`/quiz/${level}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div
        className="card"
        style={{
          padding: "2rem 2.5rem",
          maxWidth: 440,
          width: "100%",
          textAlign: "center",
        }}
      >
        <p className="muted" style={{ marginBottom: 8 }}>
          {levelLabel(level)}测试
        </p>
        <h1 style={{ marginTop: 0, marginBottom: 28 }}>准备开始</h1>
        {err && (
          <p style={{ color: "#c0392b", fontSize: "0.9rem" }}>{err}</p>
        )}
        <button
          type="button"
          className="btn-primary"
          style={{ width: "100%", marginBottom: 16 }}
          disabled={loading}
          onClick={() => void onStart()}
        >
          {loading ? "加载题目…" : "开始测试"}
        </button>
        <Link to="/">
          <button type="button" className="btn-ghost">
            回到首页
          </button>
        </Link>
      </div>
    </div>
  );
}
