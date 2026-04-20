import { cosImageUrl } from "../api/client";
import type { QuestionNameToImage as QType } from "../api/types";

type Props = {
  q: QType;
  selectedId: number | null;
  revealed: boolean;
  onSelect: (characterId: number) => void;
};

export default function QuestionNameToImage({
  q,
  selectedId,
  revealed,
  onSelect,
}: Props) {
  return (
    <div style={{ width: "100%", maxWidth: 720, margin: "0 auto" }}>
      <p style={{ textAlign: "center", marginBottom: 16, fontSize: "1.05rem" }}>
        以下哪个 coser 是 <strong>{q.main_series}</strong> 中的{" "}
        <strong>{q.name_cn}</strong>？
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
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
                padding: 4,
                border,
                background: bg,
                borderRadius: 12,
                cursor: revealed ? "default" : "pointer",
              }}
            >
              <div
                style={{
                  aspectRatio: "9 / 16",
                  borderRadius: 8,
                  overflow: "hidden",
                  background: "#1a1a1a",
                }}
              >
                <img
                  src={cosImageUrl(opt.cos_image_id)}
                  alt=""
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "contain",
                    objectPosition: "center top",
                    display: "block",
                  }}
                />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
