from __future__ import annotations

import base64
import io
import os
import random
import re
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
from openai import OpenAI
from openai import BadRequestError, OpenAIError
from PIL import Image

from app import data, quiz
from app.data import COS_SERVE_DIRS, PORTRAIT_DIR, REGEN_TMP_DIR, REPO_ROOT
from app.schemas import (
    BannerResponse,
    CertificateQrResponse,
    ExploreCharacter,
    ExploreSearchItem,
    ExploreSearchResponse,
    FeedbackBody,
    Level,
    PlaceholderResponse,
    QuizResponse,
    QuizSubmitBody,
    QuizSubmitResponse,
    RegenerateCosBody,
    RegenerateCosResponse,
)

ERNIE_SIZES: set[str] = {
    "1024x1024",
    "1376x768",
    "1264x848",
    "1200x896",
    "896x1200",
    "848x1264",
    "768x1376",
}

ERNIE_EXTRA_BODY = {
    "seed": 42,
    "use_pe": True,
    "num_inference_steps": 8,
    "guidance_scale": 1.0,
}


def _row_name_ja(row: dict) -> str | None:
    raw = row.get("name_ja")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    return str(raw)


def _row_to_explore_character(cid: int, row: dict) -> ExploreCharacter:
    name_ja = _row_name_ja(row)

    img = row.get("image_url")
    bgm_image_url = str(img) if img else None

    similar_ids = _similar_neighbor_ids(cid, row)
    similar_items: list[ExploreSearchItem] = []
    for nid in similar_ids:
        nrow = data.CHAR_ALL.get(nid)
        if nrow is None:
            continue
        similar_items.append(
            ExploreSearchItem(
                character_id=nid,
                name_cn=str(nrow.get("name_cn", "")),
                name_ja=_row_name_ja(nrow),
                main_series=str(nrow.get("main_series", "")),
                rank=int(nrow.get("rank", 0)),
            )
        )

    return ExploreCharacter(
        character_id=cid,
        name_cn=str(row.get("name_cn", "")),
        name_ja=name_ja,
        main_series=str(row.get("main_series", "")),
        summary=str(row.get("summary", "")),
        diffusion_prompt=str(row.get("diffusion_prompt", "")),
        rank=int(row.get("rank", 0)),
        bgm_image_url=bgm_image_url,
        has_cos_image=cid in data.COS_IDS,
        has_local_portrait=cid in data.PORTRAIT_IDS,
        similar_ids=similar_ids,
        similar_items=similar_items,
    )


def _similar_neighbor_ids(cid: int, row: dict) -> list[int]:
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
            if nid != cid and nid in data.CHAR_ALL:
                pool.add(nid)
    lst = list(pool)
    random.shuffle(lst)
    return lst[:6]


def _explore_character_by_id(cid: int) -> ExploreCharacter | None:
    row = data.CHAR_ALL.get(cid)
    if row is None:
        return None
    return _row_to_explore_character(cid, row)

app = FastAPI(title="simple-ani-quiz API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    data.init_data()


portrait_mount = PORTRAIT_DIR


@app.get("/images/cos/{character_id}.jpg")
def serve_cos_image(character_id: int) -> FileResponse:
    for base in COS_SERVE_DIRS:
        path = base / f"{character_id}.jpg"
        if path.is_file():
            return FileResponse(path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="cos image not found")


_REGEN_FILENAME_RE = re.compile(r"^\d+_\d+\.jpg$")


@app.get("/images/regen/{filename}")
def serve_regen_image(filename: str) -> FileResponse:
    if not _REGEN_FILENAME_RE.fullmatch(filename):
        raise HTTPException(status_code=400, detail="invalid filename")
    path = REGEN_TMP_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="regen image not found")
    return FileResponse(path, media_type="image/jpeg")


if portrait_mount.is_dir():
    app.mount(
        "/images/portrait",
        StaticFiles(directory=str(portrait_mount)),
        name="portraits",
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "repo": str(REPO_ROOT)}


@app.get("/api/explore/character/{character_id}", response_model=ExploreCharacter)
def get_explore_character(character_id: int) -> ExploreCharacter:
    out = _explore_character_by_id(character_id)
    if out is None:
        raise HTTPException(status_code=404, detail="character not found")
    return out


@app.get("/api/explore/random", response_model=ExploreCharacter)
def get_explore_random() -> ExploreCharacter:
    ids = data.ALL_CHARACTER_IDS
    if not ids:
        raise HTTPException(status_code=503, detail="no character data")
    cid = random.choice(ids)
    row = data.CHAR_ALL[cid]
    return _row_to_explore_character(cid, row)


@app.get("/api/explore/search", response_model=ExploreSearchResponse)
def explore_search(q: str, limit: int = 20) -> ExploreSearchResponse:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="q must not be empty")
    lim = max(1, min(limit, 50))
    needle = query.casefold()
    matches: list[tuple[int, dict]] = []
    for cid, row in data.CHAR_ALL.items():
        name_cn = str(row.get("name_cn", ""))
        main_series = str(row.get("main_series", ""))
        if needle in name_cn.casefold() or needle in main_series.casefold():
            matches.append((cid, row))
    matches.sort(key=lambda t: int(t[1].get("rank", 999999)))
    items: list[ExploreSearchItem] = []
    for cid, row in matches[:lim]:
        items.append(
            ExploreSearchItem(
                character_id=cid,
                name_cn=str(row.get("name_cn", "")),
                name_ja=_row_name_ja(row),
                main_series=str(row.get("main_series", "")),
                rank=int(row.get("rank", 0)),
            )
        )
    return ExploreSearchResponse(query=query, items=items)


def _normalize_prompt(raw: str) -> str:
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


def _bytes_to_jpeg(image_bytes: bytes, dest: Path) -> None:
    img = Image.open(io.BytesIO(image_bytes))
    rgb = img.convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(dest, format="JPEG", quality=95)


@app.post("/api/explore/regenerate", response_model=RegenerateCosResponse)
def regenerate_cos(body: RegenerateCosBody) -> RegenerateCosResponse:
    if body.size not in ERNIE_SIZES:
        raise HTTPException(status_code=400, detail="unsupported size")

    api_key = (body.api_key or "").strip()
    if not api_key:
        load_dotenv(REPO_ROOT / ".env")
        api_key = os.environ.get("AISTUDIO_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=401, detail="missing api key")

    prompt = _normalize_prompt(body.prompt or "")
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="prompt must not be empty")

    client = OpenAI(api_key=api_key, base_url="https://aistudio.baidu.com/llm/lmapi/v3")
    filename = f"{body.character_id}_{int(time.time())}.jpg"
    dest = REGEN_TMP_DIR / filename

    try:
        img = client.images.generate(
            model="ernie-image-turbo",
            prompt=prompt,
            n=1,
            response_format="b64_json",
            size=body.size,
            extra_body=dict(ERNIE_EXTRA_BODY),
        )
        item = img.data[0]
        b64 = getattr(item, "b64_json", None)
        if not b64:
            raise HTTPException(status_code=502, detail="missing b64_json in response")
        raw = base64.b64decode(b64)
        _bytes_to_jpeg(raw, dest)
        return RegenerateCosResponse(ok=True, image_url=f"/images/regen/{filename}")
    except BadRequestError as e:
        msg: str | None = None
        body_obj = getattr(e, "body", None)
        if isinstance(body_obj, dict):
            msg = body_obj.get("errorMsg") or body_obj.get("error_msg")
        raise HTTPException(status_code=400, detail=msg or str(e)) from e
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@app.get("/api/banner", response_model=BannerResponse)
def get_banner(limit: int = 60) -> BannerResponse:
    ids = data.top200_cos_ids()
    if not ids:
        return BannerResponse(cos_image_ids=[])
    random.shuffle(ids)
    return BannerResponse(cos_image_ids=ids[: min(limit, len(ids))])


@app.get("/api/quiz", response_model=QuizResponse)
def get_quiz(level: Level, n: int = 10) -> QuizResponse:
    if n < 1 or n > 50:
        raise HTTPException(status_code=400, detail="n must be 1..50")
    try:
        return quiz.generate_quiz(level, n=n)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/quiz/submit", response_model=QuizSubmitResponse)
def submit_quiz(body: QuizSubmitBody) -> QuizSubmitResponse:
    return QuizSubmitResponse(received_score=body.score)


@app.post("/api/feedback", response_model=PlaceholderResponse)
def feedback(_body: FeedbackBody) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content=PlaceholderResponse(
            ok=False, message="feedback not implemented"
        ).model_dump(),
    )


@app.get("/api/certificate/{session_id}/qrcode", response_model=CertificateQrResponse)
def certificate_qr(session_id: str) -> CertificateQrResponse:
    _ = session_id
    return CertificateQrResponse(ok=False, message="not implemented")
