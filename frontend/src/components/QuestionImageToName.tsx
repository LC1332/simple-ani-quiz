import { cosImageUrl } from "../api/client";
import type { QuestionImageToName as QType } from "../api/types";

type Props = {
  q: QType;
  selectedId: number | null;
  revealed: boolean;
  onSelect: (characterId: number) => void;
};

export default function QuestionImageToName({
  q,
  selectedId,
  revealed,
  onSelect,
}: Props) {
  return (
    <div style={{ width: "100%", maxWidth: 560, margin: "0 auto" }}>
      <p style={{ textAlign: "center", marginBottom: 12, fontSize: "1.05rem" }}>
        图中的 coser 在 cos 什么角色？
      </p>
      <div
        style={{
          borderRadius: 16,
          marginBottom: 16,
          background: "#1a1a1a",
          maxHeight: "min(52vh, 460px)",
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "center",
          overflow: "hidden",
        }}
      >
        <img
          src={cosImageUrl(q.cos_image_id)}
          alt="题目配图"
          style={{
            maxWidth: "100%",
            maxHeight: "min(52vh, 460px)",
            width: "auto",
            height: "auto",
            objectFit: "contain",
            objectPosition: "center top",
            display: "block",
          }}
        />
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 10,
        }}
      >
        {q.options.map((opt) => {
          const isSel = selectedId === opt.character_id;
          const isAns = opt.character_id === q.answer_character_id;
          let border = "1px solid #ddd";
          let bg = "#fff";
          if (revealed) {
            if (isAns) {
              border = "2px solid #27ae60";
              bg = "rgba(39, 174, 96, 0.12)";
            } else if (isSel && !isAns) {
              border = "2px solid #c0392b";
              bg = "rgba(192, 57, 43, 0.08)";
            }
          } else if (isSel) {
            border = "2px solid #6c5ce7";
            bg = "rgba(108, 92, 231, 0.08)";
          }
          return (
            <button
              type="button"
              key={opt.character_id}
              disabled={revealed}
              onClick={() => onSelect(opt.character_id)}
              className="card"
              style={{
                textAlign: "left",
                padding: "10px 12px",
                border,
                background: bg,
                cursor: revealed ? "default" : "pointer",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: "1rem" }}>
                {opt.name_cn}
              </div>
              <div style={{ fontSize: "0.78rem", color: "#666", marginTop: 4 }}>
                {opt.main_series}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
