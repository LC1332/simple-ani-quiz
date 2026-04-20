type Props = {
  score: number;
  passAt?: number;
};

export default function ScoreBar({ score, passAt = 50 }: Props) {
  const clamped = Math.max(0, Math.min(100, score));
  const pct = `${clamped}%`;
  const passPct = `${passAt}%`;
  return (
    <div style={{ width: "100%", maxWidth: 480, margin: "0 auto 1rem" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 12,
          color: "#666",
          marginBottom: 4,
        }}
      >
        <span>得分 {score}</span>
        <span>达标线 {passAt}</span>
      </div>
      <div
        style={{
          position: "relative",
          height: 12,
          borderRadius: 8,
          background: "linear-gradient(90deg, #eee, #e8e8e8)",
          overflow: "visible",
        }}
      >
        <div
          style={{
            height: "100%",
            width: pct,
            borderRadius: 8,
            background:
              clamped >= passAt
                ? "linear-gradient(90deg, #27ae60, #2ecc71)"
                : "linear-gradient(90deg, #6c5ce7, #a29bfe)",
            transition: "width 0.25s ease",
          }}
        />
        <div
          style={{
            position: "absolute",
            top: -2,
            left: passPct,
            width: 2,
            height: 16,
            background: "#333",
            borderRadius: 1,
            transform: "translateX(-1px)",
          }}
        />
      </div>
    </div>
  );
}
