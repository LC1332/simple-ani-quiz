import { cosImageUrl } from "../api/client";

type Props = {
  ids: number[];
  direction: "down" | "up";
};

export default function SideBanner({ ids, direction }: Props) {
  if (ids.length === 0) {
    return (
      <div
        className="side-banner-empty card"
        style={{ width: 112, minHeight: 280, flexShrink: 0 }}
      />
    );
  }
  const loop = [...ids, ...ids];
  const anim = direction === "up" ? "banner-scroll-up" : "banner-scroll-down";
  return (
    <div
      className="side-banner card"
      style={{
        width: 112,
        height: "min(70vh, 520px)",
        overflow: "hidden",
        flexShrink: 0,
        padding: 0,
      }}
    >
      <div className={`side-banner-track ${anim}`}>
        {loop.map((id, i) => (
          <div
            key={`${id}-${i}`}
            style={{
              width: "100%",
              aspectRatio: "768 / 1376",
              borderRadius: 8,
              overflow: "hidden",
              marginBottom: 8,
              background: "#1a1a1a",
            }}
          >
            <img
              src={cosImageUrl(id)}
              alt=""
              loading="lazy"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                objectPosition: "center top",
                display: "block",
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
