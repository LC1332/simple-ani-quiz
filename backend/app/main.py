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
    FeedbackBody,
    Level,
    PlaceholderResponse,
    QuizResponse,
    QuizSubmitBody,
    QuizSubmitResponse,
)

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
