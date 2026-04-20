import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchBanner } from "../api/client";
import SideBanner from "../components/SideBanner";

export default function HomePage() {
  const [leftIds, setLeftIds] = useState<number[]>([]);
  const [rightIds, setRightIds] = useState<number[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const ids = await fetchBanner(60);
        if (cancelled) return;
        const mid = Math.ceil(ids.length / 2);
        setLeftIds(ids.slice(0, mid));
        setRightIds(ids.slice(mid));
      } catch {
        setLeftIds([]);
        setRightIds([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div
      style={{
        display: "flex",
        width: "100%",
        maxWidth: 1100,
        margin: "0 auto",
        gap: 16,
        alignItems: "stretch",
        justifyContent: "center",
        padding: "1rem",
      }}
    >
      <SideBanner ids={leftIds} direction="down" />
      <main className="app-shell" style={{ flex: 1, minWidth: 0, padding: 0 }}>
        <h1 style={{ marginTop: 0, marginBottom: 8, textAlign: "center" }}>
          二次元分级测试
        </h1>
        <p className="muted" style={{ textAlign: "center", marginBottom: 28 }}>
          通过 cos 图与角色名，测测你的二次元浓度
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: 14,
            width: "100%",
            maxWidth: 420,
            margin: "0 auto",
          }}
        >
          <Link to="/start/easy" className="card" style={{ padding: "1.25rem" }}>
            <h2 style={{ margin: "0 0 8px", fontSize: "1.15rem" }}>初级</h2>
            <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
              Top 1–200 角色
            </p>
          </Link>
          <Link
            to="/start/medium"
            className="card"
            style={{ padding: "1.25rem" }}
          >
            <h2 style={{ margin: "0 0 8px", fontSize: "1.15rem" }}>中级</h2>
            <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
              Top 201–800 角色
            </p>
          </Link>
          <Link to="/start/hard" className="card" style={{ padding: "1.25rem" }}>
            <h2 style={{ margin: "0 0 8px", fontSize: "1.15rem" }}>高级</h2>
            <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
              Top 801–2600 角色
            </p>
          </Link>
          <Link to="/explore" className="card" style={{ padding: "1.25rem" }}>
            <h2 style={{ margin: "0 0 8px", fontSize: "1.15rem" }}>探索</h2>
            <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
              更多玩法（开发中）
            </p>
          </Link>
        </div>
      </main>
      <SideBanner ids={rightIds} direction="up" />
    </div>
  );
}
