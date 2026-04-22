from __future__ import annotations

import base64
import io
import json
import os
import logging
import time
import urllib.request
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
from tqdm import tqdm

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
REPO_ROOT = SCRIPTS_DIR.parent
JSONL_PATH = REPO_ROOT / "local_data" / "characters_top15000.jsonl"
OUT_DIR = REPO_ROOT / "local_data" / "ernie-image"
LEGACY_TXT2IMG_DIR = REPO_ROOT / "local_data" / "z_image_txt2img"
NSFW_REMOVE_LIST = REPO_ROOT / "data" / "remove_nsfw_list.jsonl"
ENV_PATH = REPO_ROOT / ".env"

EXTRA_BODY = {
    "seed": 42,
    "use_pe": True,
    "num_inference_steps": 8,
    "guidance_scale": 1.0,
}


def ensure_out_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def cos_jpg_path(character_id: int) -> Path:
    return OUT_DIR / f"{character_id}.jpg"


def has_cos_jpg(character_id: int) -> bool:
    p = cos_jpg_path(character_id)
    return p.is_file() and p.stat().st_size > 0


def has_z_image_txt2img_jpg(character_id: int) -> bool:
    p = LEGACY_TXT2IMG_DIR / f"{character_id}.jpg"
    return p.is_file() and p.stat().st_size > 0


def has_cos_in_ernie_or_txt2img(character_id: int) -> bool:
    """True if quiz-visible cos exists (ernie-image or z_image_txt2img only; not z_image_nsfw)."""
    return has_cos_jpg(character_id) or has_z_image_txt2img_jpg(character_id)


def load_nsfw_remove_ids(path: Path | None = None) -> list[int]:
    p = path or NSFW_REMOVE_LIST
    ids: list[int] = []
    if not p.is_file():
        logger.warning("NSFW remove list missing: %s", p)
        return ids
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                ids.append(int(obj["id"]))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                logger.warning("skip invalid remove line: %s (%s)", line[:80], e)
    seen: set[int] = set()
    out: list[int] = []
    for i in ids:
        if i in seen:
            continue
        seen.add(i)
        out.append(i)
    return out


def jsonl_ids_missing_both_cos_dirs(rows: dict[int, dict]) -> list[int]:
    """character_id in JSONL with no jpg under ernie-image nor z_image_txt2img."""
    missing: list[int] = []
    for cid in rows:
        if not has_cos_in_ernie_or_txt2img(cid):
            missing.append(cid)
    missing.sort()
    return missing


def normalize_prompt(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    parts = [p.strip() for p in s.split(",")]
    if not parts:
        return ""
    first = parts[0]
    second = parts[1] if len(parts) > 1 else ""

    def has_cosplay(x: str) -> bool:
        return "cosplay" in x.casefold()

    if not has_cosplay(first) and not has_cosplay(second):
        parts[0] = f"{first} cosplay"
    return ", ".join(parts)


def load_dotenv_api_key() -> str:
    load_dotenv(ENV_PATH)
    key = os.environ.get("AISTUDIO_API_KEY", "").strip()
    if not key:
        raise RuntimeError(f"Missing AISTUDIO_API_KEY in environment or {ENV_PATH}")
    return key


def make_client() -> OpenAI:
    return OpenAI(
        api_key=load_dotenv_api_key(),
        base_url="https://aistudio.baidu.com/llm/lmapi/v3",
    )


def load_all_rows() -> dict[int, dict]:
    if not JSONL_PATH.is_file():
        raise FileNotFoundError(f"Missing {JSONL_PATH}")
    out: dict[int, dict] = {}
    with JSONL_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            cid = int(row["character_id"])
            out[cid] = row
    return out


def rows_ranked_1_2600(rows: dict[int, dict]) -> list[tuple[int, dict]]:
    pairs: list[tuple[int, dict, int]] = []
    for cid, row in rows.items():
        try:
            r = int(row.get("rank", 0))
        except (TypeError, ValueError):
            continue
        if 1 <= r <= 2600:
            pairs.append((cid, row, r))
    pairs.sort(key=lambda t: (t[2], t[0]))
    return [(cid, row) for cid, row, _ in pairs]


def _knn_union_ids(row: dict) -> set[int]:
    cid = int(row["character_id"])
    pool: set[int] = set()
    for key in ("knn_by_character_image", "knn_by_cos_prompt"):
        raw = row.get(key) or []
        if not isinstance(raw, list):
            continue
        for x in raw:
            try:
                nid = int(x)
            except (TypeError, ValueError):
                continue
            if nid != cid:
                pool.add(nid)
    return pool


def distractor_ids_for_quiz(rows: dict[int, dict]) -> set[int]:
    """All neighbor ids referenced by rank 1..2600 rows (KNN union), restricted to ids present in rows."""
    d: set[int] = set()
    for cid, row in rows.items():
        try:
            r = int(row.get("rank", 0))
        except (TypeError, ValueError):
            continue
        if not (1 <= r <= 2600):
            continue
        for nid in _knn_union_ids(row):
            if nid in rows:
                d.add(nid)
    return d


def _bytes_to_jpeg(image_bytes: bytes, dest: Path) -> None:
    img = Image.open(io.BytesIO(image_bytes))
    rgb = img.convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(dest, format="JPEG", quality=95)


def _download_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "simple-ani-quiz-ernie-cos/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def generate_cos_jpg(
    client: OpenAI,
    character_id: int,
    prompt: str,
    *,
    max_retries: int = 5,
    sleep_base: float = 2.0,
) -> bool:
    if not prompt.strip():
        logger.warning("skip character_id=%s: empty prompt", character_id)
        return False
    dest = cos_jpg_path(character_id)
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            img = client.images.generate(
                model="ernie-image-turbo",
                prompt=prompt,
                n=1,
                response_format="b64_json",
                size="768x1376",
                extra_body=dict(EXTRA_BODY),
            )
            item = img.data[0]
            b64 = getattr(item, "b64_json", None)
            if b64:
                raw = base64.b64decode(b64)
                _bytes_to_jpeg(raw, dest)
                return True
            url = getattr(item, "url", None)
            if url:
                raw = _download_url(str(url))
                _bytes_to_jpeg(raw, dest)
                return True
            raise RuntimeError("response has neither b64_json nor url")
        except Exception as e:
            last_err = e
            logger.warning(
                "character_id=%s attempt %s/%s failed: %s",
                character_id,
                attempt + 1,
                max_retries,
                e,
            )
            if attempt + 1 < max_retries:
                time.sleep(sleep_base * (2**attempt))
    logger.error("character_id=%s giving up: %s", character_id, last_err)
    return False


def run_ids(
    client: OpenAI,
    rows: dict[int, dict],
    ids: Iterable[int],
    desc: str,
    *,
    force_regenerate: set[int] | None = None,
) -> tuple[int, int, int]:
    """
    Generate cos JPG under ernie-image. Skips when output already exists unless
    character_id is in force_regenerate (overwrite).
    """
    ensure_out_dir()
    ok = skip = fail = 0
    fr = force_regenerate or set()
    id_list = list(ids)
    for cid in tqdm(id_list, desc=desc):
        if cid not in fr and has_cos_jpg(cid):
            skip += 1
            continue
        row = rows.get(cid)
        if row is None:
            logger.warning("skip character_id=%s: not in jsonl", cid)
            fail += 1
            continue
        raw_prompt = str(row.get("diffusion_prompt", "") or "")
        prompt = normalize_prompt(raw_prompt)
        if generate_cos_jpg(client, cid, prompt):
            ok += 1
        else:
            fail += 1
    return ok, skip, fail
