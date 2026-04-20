import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { cosImageUrl, portraitUrl } from "../api/client";
import type { Level } from "../api/types";
import {
  buildReport,
  levelLabel,
  useSessionStore,
} from "../store/session";

const LEVELS = new Set<Level>(["easy", "medium", "hard"]);

export default function ReportPage() {
  const { level: raw } = useParams();
  const navigate = useNavigate();
  const level = raw && LEVELS.has(raw as Level) ? (raw as Level) : null;
  const questions = useSessionStore((s) => s.questions);
  const outcomes = useSessionStore((s) => s.outcomes);
  const score = useSessionStore((s) => s.score);
  const clear = useSessionStore((s) => s.clear);

  const [imgErr, setImgErr] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (!level) {
      navigate("/", { replace: true });
    }
  }, [level, navigate]);

  const reportItems = useMemo(
    () => buildReport(questions, outcomes),
    [questions, outcomes],
  );

  const seriesUnique = useMemo(() => {
    const s = new Set<string>();
    reportItems.forEach((r) => s.add(r.main_series));
    return [...s];
  }, [reportItems]);

  useEffect(() => {
    if (!level) return;
    if (questions.length === 0) {
      navigate(`/start/${level}`, { replace: true });
    }
  }, [level, questions.length, navigate]);

  if (!level || questions.length === 0) {
    return null;
  }

  const passed = score >= 50;

  return (
    <div className="app-shell">
      <div
        className="card"
        style={{
          padding: "2rem",
          maxWidth: 640,
          width: "100%",
        }}
      >
        <h1 style={{ marginTop: 0, textAlign: "center" }}>
          {passed
            ? `恭喜你完成 ${levelLabel(level)} 二次元测试`
            : `你做完了 ${levelLabel(level)} 二次元测试`}
        </h1>
        <p style={{ textAlign: "center", fontSize: "1.25rem", marginBottom: 8 }}>
          得分：<strong>{score}</strong> / 100
        </p>
        {passed ? (
          <p style={{ textAlign: "center", color: "#27ae60", fontWeight: 600 }}>
            已通过（≥50 分）
          </p>
        ) : (
          <p style={{ textAlign: "center", color: "#888" }}>未达 50 分达标线</p>
        )}

        <h2 style={{ fontSize: "1.05rem", marginTop: 28, marginBottom: 8 }}>
          正确识别的番剧
        </h2>
        {seriesUnique.length === 0 ? (
          <p className="muted">暂无</p>
        ) : (
          <ul style={{ margin: 0, paddingLeft: "1.2rem" }}>
            {seriesUnique.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        )}

        <h2 style={{ fontSize: "1.05rem", marginTop: 24, marginBottom: 8 }}>
          答对的角色
        </h2>
        {reportItems.length === 0 ? (
          <p className="muted">暂无</p>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
              gap: 12,
            }}
          >
            {reportItems.map((r) => (
              <div key={r.character_id} className="card" style={{ padding: 8 }}>
                <div
                  style={{
                    aspectRatio: "3 / 4",
                    borderRadius: 8,
                    overflow: "hidden",
                    background: "#1a1a1a",
                    marginBottom: 6,
                  }}
                >
                  <img
                    src={
                      imgErr[r.character_id]
                        ? cosImageUrl(r.character_id)
                        : portraitUrl(r.character_id)
                    }
                    alt=""
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "contain",
                      objectPosition: "center top",
                    }}
                    onError={() =>
                      setImgErr((prev) => ({ ...prev, [r.character_id]: true }))
                    }
                  />
                </div>
                <div style={{ fontSize: "0.9rem", fontWeight: 600 }}>
                  {r.name_cn}
                </div>
                <div className="muted" style={{ fontSize: "0.75rem" }}>
                  {r.main_series}
                </div>
              </div>
            ))}
          </div>
        )}

        <div style={{ marginTop: 28, textAlign: "center" }}>
          <Link to="/">
            <button
              type="button"
              className="btn-primary"
              onClick={() => clear()}
            >
              回到主页
            </button>
          </Link>
        </div>
      </div>
    </div>
  );
}
