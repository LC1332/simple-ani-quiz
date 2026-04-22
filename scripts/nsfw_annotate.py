#!/usr/bin/env python3
"""
本地 NSFW 候选标注：FastAPI + 内联 HTML。
在仓库根目录执行: python scripts/nsfw_annotate.py --port 8765
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import threading
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DATA = REPO_ROOT / "local_data"
JSONL_PATH = LOCAL_DATA / "characters_top15000.jsonl"
COS_DIR = LOCAL_DATA / "z_image_txt2img"
NSFW_DIR = LOCAL_DATA / "z_image_nsfw"
DATA_DIR = REPO_ROOT / "data"
REMOVE_LIST_PATH = DATA_DIR / "remove_nsfw_list.jsonl"

PROMPT_SUBSTR = "ge breast"

_lock = threading.Lock()
_by_id: dict[int, dict[str, Any]] = {}
_marked_ids: set[int] = set()
_pending: list[int] = []
_pending_set: set[int] = set()
_enqueue_origin: dict[int, str] = {}  # prompt_rule | knn | manual


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_jsonl_characters(path: Path) -> dict[int, dict[str, Any]]:
    by_id: dict[int, dict[str, Any]] = {}
    if not path.is_file():
        raise FileNotFoundError(f"Missing: {path}")
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            cid = int(row["character_id"])
            by_id[cid] = row
    return by_id


def _load_marked_ids_from_remove_list(path: Path) -> set[int]:
    ids: set[int] = set()
    if not path.is_file():
        return ids
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                ids.add(int(obj["id"]))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
    return ids


def _append_remove_line(path: Path, record: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def _cos_jpg(cid: int) -> Path:
    return COS_DIR / f"{cid}.jpg"


def _nsfw_jpg(cid: int) -> Path:
    return NSFW_DIR / f"{cid}.jpg"


def _has_displayable_image(cid: int) -> bool:
    return _cos_jpg(cid).is_file() or _nsfw_jpg(cid).is_file()


def _prompt_rule_match(row: dict[str, Any]) -> bool:
    prompt = (row.get("diffusion_prompt") or "").lower()
    return PROMPT_SUBSTR in prompt


def _knn_ids(row: dict[str, Any]) -> list[int]:
    out: list[int] = []
    for key in ("knn_by_character_image", "knn_by_cos_prompt"):
        raw = row.get(key) or []
        if not isinstance(raw, list):
            continue
        for x in raw:
            try:
                out.append(int(x))
            except (TypeError, ValueError):
                continue
    return out


def _try_enqueue(cid: int, origin: str) -> None:
    if cid in _marked_ids:
        return
    if cid in _pending_set:
        return
    if not _has_displayable_image(cid):
        return
    _pending.append(cid)
    _pending_set.add(cid)
    if cid not in _enqueue_origin:
        _enqueue_origin[cid] = origin


def _remove_from_pending(cid: int) -> None:
    if cid not in _pending_set:
        return
    _pending_set.discard(cid)
    try:
        _pending.remove(cid)
    except ValueError:
        pass


def _seed_prompt_rule() -> None:
    for cid, row in _by_id.items():
        if not _prompt_rule_match(row):
            continue
        if not _cos_jpg(cid).is_file():
            continue
        _try_enqueue(cid, "prompt_rule")


def _expand_knn_for_marked_ids(marked: Iterable[int]) -> None:
    for mid in marked:
        row = _by_id.get(mid)
        if not row:
            continue
        for nid in _knn_ids(row):
            _try_enqueue(nid, "knn")


def init_state() -> None:
    global _by_id, _marked_ids, _pending, _pending_set, _enqueue_origin
    _by_id = _load_jsonl_characters(JSONL_PATH)
    _marked_ids = _load_marked_ids_from_remove_list(REMOVE_LIST_PATH)
    _pending = []
    _pending_set = set()
    _enqueue_origin = {}

    _seed_prompt_rule()
    _expand_knn_for_marked_ids(sorted(_marked_ids))


app = FastAPI(title="nsfw-annotate", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    NSFW_DIR.mkdir(parents=True, exist_ok=True)
    init_state()


class MarkBody(BaseModel):
    id: int = Field(..., description="character_id")


class SkipBody(BaseModel):
    id: int


@app.get("/api/candidates")
def get_candidates(offset: int = 0, limit: int = 24) -> dict[str, Any]:
    if offset < 0 or limit < 1 or limit > 100:
        raise HTTPException(400, "offset>=0, limit in 1..100")
    with _lock:
        total_pending = len(_pending)
        total_marked = len(_marked_ids)
        slice_ids = _pending[offset : offset + limit]
        items: list[dict[str, Any]] = []
        for cid in slice_ids:
            row = _by_id.get(cid) or {}
            prompt = row.get("diffusion_prompt") or ""
            excerpt = prompt if len(prompt) <= 200 else prompt[:200] + "…"
            items.append(
                {
                    "id": cid,
                    "name_cn": row.get("name_cn") or "",
                    "name_ja": row.get("name_ja") or "",
                    "main_series": row.get("main_series") or "",
                    "prompt_excerpt": excerpt,
                    "enqueue_source": _enqueue_origin.get(cid, "manual"),
                    "image_url": f"/image/{cid}.jpg",
                }
            )
    return {
        "items": items,
        "total_pending": total_pending,
        "total_marked": total_marked,
        "offset": offset,
        "limit": limit,
    }


@app.post("/api/mark")
def post_mark(body: MarkBody) -> dict[str, Any]:
    cid = body.id
    with _lock:
        if cid in _marked_ids:
            raise HTTPException(400, f"id {cid} already marked")
        if cid not in _pending_set:
            raise HTTPException(400, f"id {cid} not in pending queue")
        origin = _enqueue_origin.get(cid, "manual")
        record = {"id": cid, "source": origin, "marked_at": _utc_now_iso()}
        _append_remove_line(REMOVE_LIST_PATH, record)
        _marked_ids.add(cid)
        _remove_from_pending(cid)
        _enqueue_origin.pop(cid, None)

        moved = False
        src = _cos_jpg(cid)
        dst = _nsfw_jpg(cid)
        if src.is_file():
            NSFW_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved = True
        elif dst.is_file():
            moved = False
        else:
            moved = False

        row = _by_id.get(cid)
        if row:
            for nid in _knn_ids(row):
                _try_enqueue(nid, "knn")

        total_pending = len(_pending)
        total_marked = len(_marked_ids)
    return {"ok": True, "id": cid, "moved": moved, "total_pending": total_pending, "total_marked": total_marked}


@app.post("/api/skip")
def post_skip(body: SkipBody) -> dict[str, Any]:
    cid = body.id
    with _lock:
        if cid not in _pending_set:
            raise HTTPException(400, f"id {cid} not in pending queue")
        _remove_from_pending(cid)
        _enqueue_origin.pop(cid, None)
        total_pending = len(_pending)
        total_marked = len(_marked_ids)
    return {"ok": True, "id": cid, "total_pending": total_pending, "total_marked": total_marked}


@app.get("/image/{character_id}.jpg")
def get_image(character_id: int) -> FileResponse:
    cos = _cos_jpg(character_id)
    if cos.is_file():
        return FileResponse(cos, media_type="image/jpeg")
    nsfw = _nsfw_jpg(character_id)
    if nsfw.is_file():
        return FileResponse(nsfw, media_type="image/jpeg")
    raise HTTPException(404, "image not found")


_INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>NSFW 候选标注</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; margin: 0; background: #111; color: #eee; }
    header {
      position: sticky; top: 0; z-index: 10;
      background: #1a1a1a; border-bottom: 1px solid #333;
      padding: 12px 16px; display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
    }
    header span { color: #888; }
    header strong { color: #7cb342; }
    button {
      cursor: pointer; border: none; border-radius: 6px; padding: 8px 14px;
      font-size: 14px; background: #333; color: #eee;
    }
    button:hover { background: #444; }
    button.danger { background: #8b2942; }
    button.danger:hover { background: #a83252; }
    button.muted { background: #2a2a2a; color: #aaa; }
    #grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 16px; padding: 16px;
    }
    .card {
      background: #1e1e1e; border-radius: 10px; overflow: hidden;
      border: 1px solid #333; display: flex; flex-direction: column;
    }
    .card img { width: 100%; aspect-ratio: 3/4; object-fit: cover; background: #222; }
    .card-body { padding: 10px 12px; flex: 1; display: flex; flex-direction: column; gap: 8px; }
    .meta { font-size: 12px; color: #aaa; line-height: 1.4; }
    .prompt { font-size: 11px; color: #777; max-height: 4.2em; overflow: hidden; }
    .actions { display: flex; gap: 8px; margin-top: auto; }
    #toast { position: fixed; bottom: 16px; right: 16px; background: #333; padding: 10px 16px; border-radius: 8px; display: none; }
    #toast.err { background: #5c1a1a; }
  </style>
</head>
<body>
  <header>
    <div>待审 <strong id="np">0</strong> <span>|</span> 已标记 <strong id="nm">0</strong></div>
    <button type="button" id="btnPrev">上一页</button>
    <button type="button" id="btnNext">下一页</button>
    <button type="button" id="btnRefresh" class="muted">刷新列表</button>
    <span style="margin-left:auto;font-size:12px;color:#666">offset: <span id="off">0</span> / limit 24</span>
  </header>
  <div id="grid"></div>
  <div id="toast"></div>
  <script>
    const LIMIT = 24;
    let offset = 0;

    function toast(msg, isErr) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.className = isErr ? 'err' : '';
      t.style.display = 'block';
      clearTimeout(t._h);
      t._h = setTimeout(() => { t.style.display = 'none'; }, 2500);
    }

    async function loadPage() {
      const r = await fetch('/api/candidates?offset=' + offset + '&limit=' + LIMIT);
      if (!r.ok) { toast('加载失败', true); return; }
      const data = await r.json();
      document.getElementById('np').textContent = data.total_pending;
      document.getElementById('nm').textContent = data.total_marked;
      document.getElementById('off').textContent = offset;
      const grid = document.getElementById('grid');
      grid.innerHTML = '';
      for (const it of data.items) {
        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.id = it.id;
        const img = document.createElement('img');
        img.src = it.image_url + '?t=' + Date.now();
        img.alt = String(it.id);
        img.loading = 'lazy';
        const body = document.createElement('div');
        body.className = 'card-body';
        body.innerHTML =
          '<div class="meta"><b>#' + it.id + '</b> ' + escapeHtml(it.name_cn) +
          '<br/>' + escapeHtml(it.main_series) +
          '<br/><span style="color:#666">来源: ' + escapeHtml(it.enqueue_source) + '</span></div>' +
          '<div class="prompt">' + escapeHtml(it.prompt_excerpt) + '</div>';
        const actions = document.createElement('div');
        actions.className = 'actions';
        const bMark = document.createElement('button');
        bMark.className = 'danger';
        bMark.textContent = '标记 NSFW';
        bMark.onclick = () => markOne(it.id, card);
        const bSkip = document.createElement('button');
        bSkip.className = 'muted';
        bSkip.textContent = '跳过';
        bSkip.onclick = () => skipOne(it.id, card);
        actions.appendChild(bMark);
        actions.appendChild(bSkip);
        body.appendChild(actions);
        card.appendChild(img);
        card.appendChild(body);
        grid.appendChild(card);
      }
      if (data.items.length === 0 && data.total_pending > 0 && offset >= data.total_pending) {
        offset = Math.max(0, Math.floor((data.total_pending - 1) / LIMIT) * LIMIT);
        return loadPage();
      }
    }

    function escapeHtml(s) {
      const d = document.createElement('div');
      d.textContent = s;
      return d.innerHTML;
    }

    async function markOne(id, cardEl) {
      const r = await fetch('/api/mark', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) { toast(j.detail || '标记失败', true); return; }
      cardEl.remove();
      toast('已标记 #' + id + (j.moved ? '，已移动' : ''));
      await maybeFillPage();
    }

    async function skipOne(id, cardEl) {
      const r = await fetch('/api/skip', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) { toast(j.detail || '跳过失败', true); return; }
      cardEl.remove();
      toast('已跳过 #' + id);
      await maybeFillPage();
    }

    async function maybeFillPage() {
      const grid = document.getElementById('grid');
      if (grid.children.length < 6) {
        const head = await fetch('/api/candidates?offset=0&limit=1');
        const h = await head.json();
        document.getElementById('np').textContent = h.total_pending;
        document.getElementById('nm').textContent = h.total_marked;
        if (h.total_pending === 0) return;
        if (offset + LIMIT > h.total_pending) {
          offset = Math.max(0, h.total_pending - LIMIT);
        }
        await loadPage();
      } else {
        const head = await fetch('/api/candidates?offset=0&limit=1');
        const h = await head.json();
        document.getElementById('np').textContent = h.total_pending;
        document.getElementById('nm').textContent = h.total_marked;
      }
    }

    document.getElementById('btnNext').onclick = async () => {
      const head = await fetch('/api/candidates?offset=0&limit=1');
      const h = await head.json();
      if (offset + LIMIT < h.total_pending) offset += LIMIT;
      else toast('已是最后一页');
      await loadPage();
    };
    document.getElementById('btnPrev').onclick = async () => {
      offset = Math.max(0, offset - LIMIT);
      await loadPage();
    };
    document.getElementById('btnRefresh').onclick = () => loadPage();

    loadPage();
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML


def main() -> None:
    parser = argparse.ArgumentParser(description="NSFW annotate local server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        import uvicorn
    except ImportError as e:
        raise SystemExit("请安装 uvicorn: pip install -r backend/requirements.txt") from e
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
