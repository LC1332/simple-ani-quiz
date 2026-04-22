import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  cosImageUrl,
  fetchExploreCharacter,
  fetchExploreRandom,
  portraitUrl,
  searchExplore,
} from "../api/client";
import type { ExploreCharacter, ExploreSearchItem } from "../api/types";

const TOKEN_STORAGE_KEY = "explore_regen_token";
const ASPECT_RATIOS = [
  "16:9",
  "3:2",
  "4:3",
  "1:1",
  "3:4",
  "2:3",
  "9:16",
] as const;

export default function ExplorePage() {
  const { id: idParam } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [char, setChar] = useState<ExploreCharacter | null>(null);
  const [loading, setLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [redirecting, setRedirecting] = useState(!idParam);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<ExploreSearchItem[]>([]);
  const searchWrapRef = useRef<HTMLDivElement>(null);

  const [portraitFailed, setPortraitFailed] = useState(false);
  const [noPortrait, setNoPortrait] = useState(false);
  const [regenPrompt, setRegenPrompt] = useState("");
  const [aspect, setAspect] = useState<(typeof ASPECT_RATIOS)[number]>("1:1");
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem(TOKEN_STORAGE_KEY) ?? "";
    } catch {
      return "";
    }
  });

  const runSearch = useCallback(async (raw: string) => {
    const q = raw.trim();
    if (!q) {
      setSearchResults([]);
      setSearchLoading(false);
      return;
    }
    setSearchLoading(true);
    try {
      const res = await searchExplore(q, 20);
      setSearchResults(res.items);
    } catch {
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => {
      void runSearch(searchQuery);
    }, 300);
    return () => clearTimeout(t);
  }, [searchQuery, runSearch]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!searchWrapRef.current?.contains(e.target as Node)) {
        setSearchOpen(false);
      }
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  useEffect(() => {
    if (idParam) return;
    let cancelled = false;
    setRedirecting(true);
    (async () => {
      try {
        const c = await fetchExploreRandom();
        if (!cancelled) navigate(`/explore/${c.character_id}`, { replace: true });
      } catch {
        if (!cancelled) {
          setRedirecting(false);
          setLoadError("无法加载随机角色，请检查网络或稍后重试。");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [idParam, navigate]);

  useEffect(() => {
    if (!idParam) return;
    const num = Number.parseInt(idParam, 10);
    if (Number.isNaN(num)) {
      setChar(null);
      setNotFound(true);
      setLoadError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setNotFound(false);
    setLoadError(null);
    (async () => {
      try {
        const c = await fetchExploreCharacter(num);
        if (cancelled) return;
        if (c === null) {
          setChar(null);
          setNotFound(true);
        } else {
          setChar(c);
        }
      } catch (e) {
        if (!cancelled) {
          setChar(null);
          setLoadError(e instanceof Error ? e.message : "加载失败");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [idParam]);

  useEffect(() => {
    setPortraitFailed(false);
    setNoPortrait(false);
    if (char) setRegenPrompt(char.diffusion_prompt);
  }, [char?.character_id]);

  useEffect(() => {
    try {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } catch {
      /* ignore */
    }
  }, [token]);

  const pickRandom = async () => {
    try {
      const c = await fetchExploreRandom();
      navigate(`/explore/${c.character_id}`);
    } catch {
      alert("随机角色加载失败，请稍后重试。");
    }
  };

  const portraitSrc = (() => {
    if (!char || noPortrait) return null;
    if (!portraitFailed) {
      if (char.has_local_portrait) return portraitUrl(char.character_id);
      return char.bgm_image_url;
    }
    return char.bgm_image_url;
  })();

  const similarRows: ExploreSearchItem[] = char
    ? (char.similar_items?.length ? char.similar_items : [])
    : [];

  const copyPrompt = async () => {
    if (!char) return;
    try {
      await navigator.clipboard.writeText(char.diffusion_prompt);
    } catch {
      alert("复制失败，请手动选择文本复制。");
    }
  };

  const cardMax: CSSProperties = { maxWidth: 760, width: "100%" };

  if (!idParam && redirecting) {
    return (
      <div className="app-shell">
        <div className="card" style={{ ...cardMax, padding: "2rem", textAlign: "center" }}>
          <p className="muted" style={{ margin: 0 }}>
            正在为你挑选一位角色…
          </p>
        </div>
      </div>
    );
  }

  if (!idParam && loadError) {
    return (
      <div className="app-shell">
        <div className="card" style={{ ...cardMax, padding: "2rem", textAlign: "center" }}>
          <p style={{ marginTop: 0 }}>{loadError}</p>
          <button type="button" className="btn-primary" onClick={() => void pickRandom()}>
            随机一位
          </button>
          <div style={{ marginTop: 16 }}>
            <Link to="/">
              <button type="button" className="btn-ghost">
                回到主页
              </button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <div style={{ ...cardMax, marginBottom: 16 }}>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 12,
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div ref={searchWrapRef} style={{ position: "relative", flex: "1 1 220px", minWidth: 0 }}>
            <input
              type="search"
              className="card"
              placeholder="按中文名或番剧名搜索…"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setSearchOpen(true);
              }}
              onFocus={() => setSearchOpen(true)}
              style={{
                width: "100%",
                padding: "0.65rem 1rem",
                borderRadius: 12,
                border: "1px solid #e8e4f0",
                fontSize: "0.95rem",
              }}
            />
            {searchOpen && (searchQuery.trim() || searchLoading) ? (
              <div
                className="card"
                style={{
                  position: "absolute",
                  zIndex: 10,
                  left: 0,
                  right: 0,
                  top: "100%",
                  marginTop: 6,
                  maxHeight: 280,
                  overflowY: "auto",
                  padding: "0.35rem 0",
                  boxShadow: "0 12px 40px rgba(80,60,120,0.15)",
                }}
              >
                {searchLoading ? (
                  <div className="muted" style={{ padding: "0.75rem 1rem" }}>
                    搜索中…
                  </div>
                ) : searchQuery.trim() && searchResults.length === 0 ? (
                  <div className="muted" style={{ padding: "0.75rem 1rem" }}>
                    无匹配结果
                  </div>
                ) : (
                  searchResults.map((item) => (
                    <Link
                      key={item.character_id}
                      to={`/explore/${item.character_id}`}
                      onClick={() => {
                        setSearchOpen(false);
                        setSearchQuery("");
                      }}
                      style={{
                        display: "block",
                        padding: "0.55rem 1rem",
                        fontSize: "0.9rem",
                        borderBottom: "1px solid rgba(0,0,0,0.04)",
                      }}
                    >
                      {item.name_cn}
                      <span className="muted" style={{ marginLeft: 8 }}>
                        · {item.main_series}
                      </span>
                    </Link>
                  ))
                )}
              </div>
            ) : null}
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" className="btn-ghost" onClick={() => void pickRandom()}>
              随机一位
            </button>
            <Link to="/">
              <button type="button" className="btn-ghost">
                回到主页
              </button>
            </Link>
          </div>
        </div>
      </div>

      <div className="card" style={{ ...cardMax, padding: "1.5rem 1.75rem" }}>
        {loading ? (
          <p className="muted" style={{ margin: 0, textAlign: "center" }}>
            加载中…
          </p>
        ) : notFound ? (
          <div style={{ textAlign: "center" }}>
            <h1 style={{ marginTop: 0, fontSize: "1.25rem" }}>未找到该角色</h1>
            <button type="button" className="btn-primary" onClick={() => void pickRandom()}>
              随机一位
            </button>
          </div>
        ) : loadError ? (
          <p style={{ margin: 0, textAlign: "center", color: "#c0392b" }}>{loadError}</p>
        ) : char ? (
          <>
            <header style={{ marginBottom: 20 }}>
              <h1 style={{ margin: "0 0 6px", fontSize: "1.65rem" }}>{char.name_cn}</h1>
              <p className="muted" style={{ margin: 0, fontSize: "1rem" }}>
                {char.main_series}
              </p>
            </header>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                gap: 14,
                marginBottom: 20,
              }}
            >
              <div>
                <div className="muted" style={{ marginBottom: 6, fontSize: "0.85rem" }}>
                  角色头像
                </div>
                {portraitSrc ? (
                  <img
                    src={portraitSrc}
                    alt=""
                    referrerPolicy="no-referrer"
                    onError={() => {
                      if (char.has_local_portrait && !portraitFailed) {
                        setPortraitFailed(true);
                      } else {
                        setNoPortrait(true);
                      }
                    }}
                    style={{
                      width: "100%",
                      maxHeight: 280,
                      objectFit: "contain",
                      borderRadius: 12,
                      background: "rgba(0,0,0,0.04)",
                    }}
                  />
                ) : (
                  <div
                    className="muted"
                    style={{
                      padding: "2rem",
                      textAlign: "center",
                      borderRadius: 12,
                      background: "rgba(0,0,0,0.04)",
                    }}
                  >
                    暂无头像
                  </div>
                )}
              </div>
              <div>
                <div className="muted" style={{ marginBottom: 6, fontSize: "0.85rem" }}>
                  Cos 图
                </div>
                {char.has_cos_image ? (
                  <img
                    src={cosImageUrl(char.character_id)}
                    alt=""
                    style={{
                      width: "100%",
                      maxHeight: 280,
                      objectFit: "contain",
                      borderRadius: 12,
                      background: "rgba(0,0,0,0.04)",
                    }}
                  />
                ) : (
                  <div
                    className="muted"
                    style={{
                      padding: "2rem",
                      textAlign: "center",
                      borderRadius: 12,
                      background: "rgba(0,0,0,0.04)",
                    }}
                  >
                    暂无本地 Cos 图
                  </div>
                )}
              </div>
            </div>

            <details style={{ marginBottom: 14 }}>
              <summary style={{ cursor: "pointer", fontWeight: 600 }}>生平</summary>
              <div
                style={{
                  marginTop: 10,
                  whiteSpace: "pre-wrap",
                  fontSize: "0.92rem",
                  lineHeight: 1.55,
                }}
              >
                {char.summary || "（无）"}
              </div>
            </details>

            <details style={{ marginBottom: 20 }}>
              <summary style={{ cursor: "pointer", fontWeight: 600 }}>Diffusion prompt</summary>
              <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
                <pre
                  style={{
                    margin: 0,
                    padding: 12,
                    borderRadius: 10,
                    background: "rgba(0,0,0,0.05)",
                    fontSize: "0.78rem",
                    overflowX: "auto",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {char.diffusion_prompt || "（无）"}
                </pre>
                <button type="button" className="btn-ghost" style={{ alignSelf: "flex-start" }} onClick={() => void copyPrompt()}>
                  复制全文
                </button>
              </div>
            </details>

            <details style={{ marginBottom: 20 }}>
              <summary style={{ cursor: "pointer", fontWeight: 600 }}>重新生成 Cos 图（预留）</summary>
              <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 12 }}>
                <label className="muted" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  Prompt
                  <textarea
                    value={regenPrompt}
                    onChange={(e) => setRegenPrompt(e.target.value)}
                    rows={5}
                    style={{
                      width: "100%",
                      padding: 10,
                      borderRadius: 10,
                      border: "1px solid #ddd",
                      fontFamily: "inherit",
                      fontSize: "0.88rem",
                    }}
                  />
                </label>
                <fieldset style={{ border: "none", margin: 0, padding: 0 }}>
                  <legend className="muted" style={{ fontSize: "0.9rem", marginBottom: 8 }}>
                    比例
                  </legend>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 14px" }}>
                    {ASPECT_RATIOS.map((r) => (
                      <label key={r} style={{ fontSize: "0.88rem", cursor: "pointer" }}>
                        <input
                          type="radio"
                          name="aspect"
                          checked={aspect === r}
                          onChange={() => setAspect(r)}
                          style={{ marginRight: 6 }}
                        />
                        {r}
                      </label>
                    ))}
                  </div>
                </fieldset>
                <label className="muted" style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  API Token（仅本地浏览器）
                  <input
                    type="password"
                    autoComplete="off"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="输入后显示为隐藏字符"
                    style={{
                      padding: "0.55rem 0.75rem",
                      borderRadius: 10,
                      border: "1px solid #ddd",
                      fontSize: "0.9rem",
                    }}
                  />
                </label>
                <button
                  type="button"
                  className="btn-primary"
                  style={{ alignSelf: "flex-start" }}
                  onClick={() => {
                    alert("接入中，敬请期待");
                  }}
                >
                  生成
                </button>
              </div>
            </details>

            {similarRows.length > 0 ? (
              <section style={{ marginBottom: 16 }}>
                <h2 style={{ fontSize: "1.05rem", margin: "0 0 10px" }}>相近角色</h2>
                <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
                  {similarRows.map((item) => (
                    <li key={item.character_id} style={{ marginBottom: 8 }}>
                      <Link
                        to={`/explore/${item.character_id}`}
                        style={{ fontSize: "0.95rem", textDecoration: "underline" }}
                      >
                        {item.name_cn}
                        <span className="muted" style={{ marginLeft: 6 }}>
                          · {item.main_series}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            <footer className="muted" style={{ fontSize: "0.75rem", textAlign: "center", marginTop: 8 }}>
              数据来自{" "}
              <a
                href={`https://bgm.tv/character/${char.character_id}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{ textDecoration: "underline", opacity: 0.85 }}
              >
                bgm.tv
              </a>
              {" · "}
              <a
                href={`https://bgm.tv/character/${char.character_id}`}
                target="_blank"
                rel="noopener noreferrer"
                style={{ textDecoration: "underline", opacity: 0.85 }}
              >
                查看原页面
              </a>
            </footer>
          </>
        ) : null}
      </div>
    </div>
  );
}
