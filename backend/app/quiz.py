from __future__ import annotations

import random
from app import data
from app.schemas import (
    ImageOption,
    NameOption,
    QuestionImageToName,
    QuestionNameToImage,
    QuizQuestion,
    QuizResponse,
    Level,
)

MAX_REGEN = 80


def _knn_union(row: dict) -> set[int]:
    img = row.get("knn_by_character_image") or []
    pr = row.get("knn_by_cos_prompt") or []
    return set(int(x) for x in img) | set(int(x) for x in pr)


def _pick_distractors_image_to_name(
    answer_id: int,
    bucket: list[int],
    need: int = 5,
) -> list[int]:
    row = data.CHAR_BY_ID[answer_id]
    pool = _knn_union(row) - {answer_id}
    pool = {cid for cid in pool if cid in data.CHAR_BY_ID}
    picked: list[int] = []
    pool_list = list(pool)
    random.shuffle(pool_list)
    for cid in pool_list:
        if len(picked) >= need:
            break
        picked.append(cid)
    # fill from bucket
    if len(picked) < need:
        rest = [c for c in bucket if c != answer_id and c not in picked]
        random.shuffle(rest)
        for c in rest:
            if len(picked) >= need:
                break
            picked.append(c)
    if len(picked) < need:
        raise ValueError("Not enough distractors for image_to_name")
    return picked[:need]


def _pick_distractors_name_to_image(answer_id: int, need: int = 5) -> list[int] | None:
    row = data.CHAR_BY_ID[answer_id]
    pool = _knn_union(row) - {answer_id}
    candidates = [cid for cid in pool if cid in data.CHAR_BY_ID and cid in data.COS_IDS]
    random.shuffle(candidates)
    if len(candidates) < need:
        return None
    return candidates[:need]


def _build_image_to_name(qid: str, answer_id: int, bucket: list[int]) -> QuestionImageToName:
    dist = _pick_distractors_image_to_name(answer_id, bucket)
    opts_ids = [answer_id] + dist
    random.shuffle(opts_ids)
    options = [
        NameOption(
            character_id=cid,
            name_cn=str(data.CHAR_BY_ID[cid]["name_cn"]),
            main_series=str(data.CHAR_BY_ID[cid]["main_series"]),
        )
        for cid in opts_ids
    ]
    return QuestionImageToName(
        id=qid,
        cos_image_id=answer_id,
        options=options,
        answer_character_id=answer_id,
    )


def _build_name_to_image(qid: str, answer_id: int) -> QuestionNameToImage | None:
    dist = _pick_distractors_name_to_image(answer_id)
    if dist is None:
        return None
    row = data.CHAR_BY_ID[answer_id]
    opts_ids = [answer_id] + dist
    random.shuffle(opts_ids)
    options = [
        ImageOption(character_id=cid, cos_image_id=cid) for cid in opts_ids
    ]
    return QuestionNameToImage(
        id=qid,
        character_id=answer_id,
        name_cn=str(row["name_cn"]),
        main_series=str(row["main_series"]),
        options=options,
        answer_character_id=answer_id,
    )


def generate_quiz(level: Level, n: int = 10) -> QuizResponse:
    bucket = data.bucket_for_level(level)
    eligible = [cid for cid in bucket if cid in data.COS_IDS]
    if len(eligible) < n:
        raise ValueError(f"Not enough characters with cos images in bucket: {len(eligible)} < {n}")

    # sample answer ids without replacement
    answer_ids = random.sample(eligible, n)
    questions: list[QuizQuestion] = []

    for i, aid in enumerate(answer_ids):
        q: QuizQuestion | None = None
        for _ in range(MAX_REGEN):
            qtype = random.choice(["image_to_name", "name_to_image"])
            if qtype == "name_to_image":
                q = _build_name_to_image(f"q{i}", aid)
                if q is not None:
                    break
            else:
                q = _build_image_to_name(f"q{i}", aid, bucket)
                if q is not None:
                    break
        if q is None:
            q = _build_image_to_name(f"q{i}", aid, bucket)
        questions.append(q)

    return QuizResponse(level=level, questions=questions)
