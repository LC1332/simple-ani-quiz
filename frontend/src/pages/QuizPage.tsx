import { useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import type { Level } from "../api/types";
import ProgressDots from "../components/ProgressDots";
import QuestionImageToName from "../components/QuestionImageToName";
import QuestionNameToImage from "../components/QuestionNameToImage";
import ScoreBar from "../components/ScoreBar";
import { levelLabel, useSessionStore } from "../store/session";

const LEVELS = new Set<Level>(["easy", "medium", "hard"]);

export default function QuizPage() {
  const { level: raw } = useParams();
  const navigate = useNavigate();
  const level = raw && LEVELS.has(raw as Level) ? (raw as Level) : null;

  const questions = useSessionStore((s) => s.questions);
  const currentIndex = useSessionStore((s) => s.currentIndex);
  const outcomes = useSessionStore((s) => s.outcomes);
  const selectedIds = useSessionStore((s) => s.selectedIds);
  const revealed = useSessionStore((s) => s.revealed);
  const score = useSessionStore((s) => s.score);
  const setSelected = useSessionStore((s) => s.setSelected);
  const confirm = useSessionStore((s) => s.confirm);
  const skip = useSessionStore((s) => s.skip);
  const next = useSessionStore((s) => s.next);

  useEffect(() => {
    if (!level) {
      navigate("/", { replace: true });
      return;
    }
    if (questions.length === 0) {
      navigate(`/start/${level}`, { replace: true });
    }
  }, [level, questions.length, navigate]);

  if (!level || questions.length === 0) {
    return null;
  }

  const q = questions[currentIndex];
  const selected = selectedIds[currentIndex] ?? null;
  const isLast = currentIndex >= questions.length - 1;

  const handleNext = () => {
    if (!revealed) return;
    if (isLast) {
      navigate(`/report/${level}`);
      return;
    }
    next();
  };

  return (
    <div className="app-shell">
      <div
        className="card"
        style={{
          padding: "1.25rem 1.5rem 1.75rem",
          width: "100%",
          maxWidth: 800,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 8,
            marginBottom: 8,
          }}
        >
          <span className="muted">
            {levelLabel(level)} · 第 {currentIndex + 1} / {questions.length} 题
          </span>
          <Link to="/" className="btn-ghost" style={{ fontSize: "0.85rem" }}>
            回到首页
          </Link>
        </div>

        <ProgressDots
          total={questions.length}
          currentIndex={currentIndex}
          outcomes={outcomes}
          revealed={revealed}
        />
        <ScoreBar score={score} passAt={50} />

        {q.type === "image_to_name" ? (
          <QuestionImageToName
            q={q}
            selectedId={selected}
            revealed={revealed}
            onSelect={(id) => setSelected(id)}
          />
        ) : (
          <QuestionNameToImage
            q={q}
            selectedId={selected}
            revealed={revealed}
            onSelect={(id) => setSelected(id)}
          />
        )}

        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 10,
            justifyContent: "center",
            marginTop: 20,
            alignItems: "center",
          }}
        >
          {!revealed && (
            <>
              <button
                type="button"
                className="btn-primary"
                disabled={selected == null}
                onClick={() => confirm()}
              >
                确定
              </button>
              <button type="button" className="btn-danger-ghost" onClick={() => skip()}>
                放弃本题
              </button>
            </>
          )}
          {revealed && (
            <button type="button" className="btn-primary" onClick={handleNext}>
              {isLast ? "查看报告" : "下一题"}
            </button>
          )}
          <button
            type="button"
            className="btn-ghost"
            disabled
            title="即将开放"
            style={{ opacity: 0.45 }}
          >
            吐槽
          </button>
        </div>
      </div>
    </div>
  );
}
