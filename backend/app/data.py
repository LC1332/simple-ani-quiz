from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_DATA = REPO_ROOT / "local_data"
JSONL_PATH = LOCAL_DATA / "characters_top15000.jsonl"
COS_DIR = LOCAL_DATA / "z_image_txt2img"
PORTRAIT_DIR = LOCAL_DATA / "character_portraits_jpg"


def _scan_cos_ids() -> set[int]:
    ids: set[int] = set()
    if not COS_DIR.is_dir():
        return ids
    for p in COS_DIR.iterdir():
        if p.suffix.lower() == ".jpg" and p.stem.isdigit():
            ids.add(int(p.stem))
    return ids


def load_characters() -> tuple[dict[int, dict], list[int], list[int], list[int], set[int]]:
    """
    Returns:
        by_id: character_id -> raw row dict (only rank <= 2600)
        bucket_easy: ids rank 1-200
        bucket_medium: ids rank 201-800
        bucket_hard: ids rank 801-2600
        cos_ids: set of character ids that have z_image_txt2img/{id}.jpg
    """
    by_id: dict[int, dict] = {}
    if not JSONL_PATH.is_file():
        raise FileNotFoundError(f"Missing data file: {JSONL_PATH}")

    with JSONL_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            rank = int(row.get("rank", 0))
            if rank < 1 or rank > 2600:
                continue
            cid = int(row["character_id"])
            by_id[cid] = row

    bucket_easy: list[int] = []
    bucket_medium: list[int] = []
    bucket_hard: list[int] = []
    for cid, row in by_id.items():
        r = int(row["rank"])
        if 1 <= r <= 200:
            bucket_easy.append(cid)
        elif 201 <= r <= 800:
            bucket_medium.append(cid)
        elif 801 <= r <= 2600:
            bucket_hard.append(cid)

    cos_ids = _scan_cos_ids()
    return by_id, bucket_easy, bucket_medium, bucket_hard, cos_ids


# Populated by init_data()
CHAR_BY_ID: dict[int, dict] = {}
BUCKET_EASY: list[int] = []
BUCKET_MEDIUM: list[int] = []
BUCKET_HARD: list[int] = []
COS_IDS: set[int] = set()


def init_data() -> None:
    global CHAR_BY_ID, BUCKET_EASY, BUCKET_MEDIUM, BUCKET_HARD, COS_IDS
    CHAR_BY_ID, BUCKET_EASY, BUCKET_MEDIUM, BUCKET_HARD, COS_IDS = load_characters()


def bucket_for_level(level: str) -> list[int]:
    if level == "easy":
        return BUCKET_EASY
    if level == "medium":
        return BUCKET_MEDIUM
    if level == "hard":
        return BUCKET_HARD
    raise ValueError(f"Unknown level: {level}")


def top200_cos_ids() -> list[int]:
    """Rank 1-200 characters that have a cos jpg."""
    return [cid for cid in BUCKET_EASY if cid in COS_IDS]
