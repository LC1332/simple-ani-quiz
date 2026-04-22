from __future__ import annotations

import random
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import data, quiz
from app.data import LOCAL_DATA, PORTRAIT_DIR, REPO_ROOT
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
)


def _row_to_explore_character(cid: int, row: dict) -> ExploreCharacter:
    name_ja_raw = row.get("name_ja")
    name_ja: str | None
    if name_ja_raw is None or (isinstance(name_ja_raw, str) and not name_ja_raw.strip()):
        name_ja = None
    else:
        name_ja = str(name_ja_raw)

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


cos_mount = LOCAL_DATA / "z_image_txt2img"
portrait_mount = PORTRAIT_DIR
if cos_mount.is_dir():
    app.mount("/images/cos", StaticFiles(directory=str(cos_mount)), name="cos_images")
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
                main_series=str(row.get("main_series", "")),
                rank=int(row.get("rank", 0)),
            )
        )
    return ExploreSearchResponse(query=query, items=items)


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
