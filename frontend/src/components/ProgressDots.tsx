import type { QuestionOutcome } from "../store/session";

type Props = {
  total: number;
  currentIndex: number;
  outcomes: (QuestionOutcome | null)[];
  revealed: boolean;
};

export default function ProgressDots({
  total,
  currentIndex,
  outcomes,
  revealed,
}: Props) {
  return (
    <div
      style={{
        display: "flex",
        gap: 8,
        justifyContent: "center",
        flexWrap: "wrap",
        marginBottom: 12,
      }}
    >
      {Array.from({ length: total }, (_, i) => {
        const o = outcomes[i];
        let bg = "#d0d0d0";
        let border = "2px solid transparent";

        if (i > currentIndex) {
          bg = "#d0d0d0";
          border = "2px solid transparent";
        } else if (i < currentIndex) {
          border = "2px solid transparent";
          if (o === "correct") bg = "#27ae60";
          else if (o === "wrong") bg = "#c0392b";
          else if (o === "skipped") bg = "#f1c40f";
        } else {
          if (!revealed) {
            bg = "transparent";
            border = "2px solid #111";
          } else {
            border = "2px solid transparent";
            if (o === "correct") {
              bg = "#27ae60";
            } else if (o === "wrong") {
              bg = "#c0392b";
            } else if (o === "skipped") {
              bg = "#f1c40f";
            }
          }
        }
        return (
          <span
            key={i}
            title={`第 ${i + 1} 题`}
            style={{
              width: 14,
              height: 14,
              borderRadius: "50%",
              background: bg,
              border,
              boxSizing: "border-box",
              display: "inline-block",
            }}
          />
        );
      })}
    </div>
  );
}
