import { Link } from "react-router-dom";

export default function ExplorePage() {
  return (
    <div className="app-shell">
      <div className="card" style={{ padding: "2rem", maxWidth: 420, textAlign: "center" }}>
        <h1 style={{ marginTop: 0 }}>探索</h1>
        <p className="muted">正在构建中，敬请期待。</p>
        <Link to="/">
          <button type="button" className="btn-primary" style={{ marginTop: 16 }}>
            回到主页
          </button>
        </Link>
      </div>
    </div>
  );
}
