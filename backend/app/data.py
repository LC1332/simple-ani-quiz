from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCAL_DATA = REPO_ROOT / "local_data"
JSONL_PATH = LOCAL_DATA / "characters_top15000.jsonl"
COS_DIR = LOCAL_DATA / "z_image_txt2img"
COS_DIR_ERNIE = LOCAL_DATA / "ernie-image"
REGEN_TMP_DIR = LOCAL_DATA / "ernie-image-regen-tmp"
PORTRAIT_DIR = LOCAL_DATA / "character_portraits_jpg"

# Prefer ernie-image for new assets; keep legacy dir for older jpg.
COS_SERVE_DIRS: tuple[Path, ...] = (COS_DIR_ERNIE, COS_DIR)


def _scan_jpg_ids(directory: Path) -> set[int]:
    ids: set[int] = set()
    if not directory.is_dir():
        return ids
    for p in directory.iterdir():
        if p.suffix.lower() == ".jpg" and p.stem.isdigit():
            ids.add(int(p.stem))
    return ids


def load_characters() -> tuple[
    dict[int, dict],
    dict[int, dict],
    list[int],
    list[int],
    list[int],
    set[int],
    set[int],
]:
    """
    Returns:
        char_all: character_id -> raw row dict (all rows in JSONL)
        by_id: character_id -> raw row dict (only rank 1..2600, for quiz)
        bucket_easy: ids rank 1-200
        bucket_medium: ids rank 201-800
        bucket_hard: ids rank 801-2600
        cos_ids: character ids with ernie-image/{id}.jpg or z_image_txt2img/{id}.jpg
        portrait_ids: character ids with character_portraits_jpg/{id}.jpg
    """
    char_all: dict[int, dict] = {}
    by_id: dict[int, dict] = {}
    if not JSONL_PATH.is_file():
        raise FileNotFoundError(f"Missing data file: {JSONL_PATH}")

    with JSONL_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            cid = int(row["character_id"])
            char_all[cid] = row
            rank = int(row.get("rank", 0))
            if 1 <= rank <= 2600:
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

    cos_ids: set[int] = set()
    for d in COS_SERVE_DIRS:
        cos_ids |= _scan_jpg_ids(d)
    portrait_ids = _scan_jpg_ids(PORTRAIT_DIR)
    return char_all, by_id, bucket_easy, bucket_medium, bucket_hard, cos_ids, portrait_ids


# Populated by init_data()
CHAR_ALL: dict[int, dict] = {}
CHAR_BY_ID: dict[int, dict] = {}
BUCKET_EASY: list[int] = []
BUCKET_MEDIUM: list[int] = []
BUCKET_HARD: list[int] = []
COS_IDS: set[int] = set()
PORTRAIT_IDS: set[int] = set()
ALL_CHARACTER_IDS: list[int] = []


def init_data() -> None:
    global CHAR_ALL, CHAR_BY_ID, BUCKET_EASY, BUCKET_MEDIUM, BUCKET_HARD
    global COS_IDS, PORTRAIT_IDS, ALL_CHARACTER_IDS
    REGEN_TMP_DIR.mkdir(parents=True, exist_ok=True)
    for p in REGEN_TMP_DIR.glob("*.jpg"):
        try:
            p.unlink()
        except OSError:
            pass
    (
        CHAR_ALL,
        CHAR_BY_ID,
        BUCKET_EASY,
        BUCKET_MEDIUM,
        BUCKET_HARD,
        COS_IDS,
        PORTRAIT_IDS,
    ) = load_characters()
    ALL_CHARACTER_IDS = list(CHAR_ALL.keys())


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
