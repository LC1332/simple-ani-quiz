#!/usr/bin/env python3
"""
为两类 id 用 ernie-image-turbo 写入 local_data/ernie-image/{id}.jpg：

1. data/remove_nsfw_list.jsonl 中的 id（在 JSONL 中有记录的）：强制覆盖已有 ernie 图，便于替换曾判为 NSFW 的图。
2. JSONL 中任意角色：在 z_image_txt2img 与 ernie-image 下均不存在 {id}.jpg 的（不含 z_image_nsfw，与后端可见 cos 一致）。

在仓库根执行:
  python3 scripts/ernie_cos/regenerate_missing_and_nsfw.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ernie_cos.common import (  # noqa: E402
    jsonl_ids_missing_both_cos_dirs,
    load_all_rows,
    load_nsfw_remove_ids,
    make_client,
    run_ids,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    rows = load_all_rows()
    nsfw_raw = load_nsfw_remove_ids()
    nsfw_in_jsonl = [i for i in nsfw_raw if i in rows]
    nsfw_not_in_jsonl = [i for i in nsfw_raw if i not in rows]
    if nsfw_not_in_jsonl:
        logging.warning(
            "remove_nsfw_list 中有 %s 个 id 不在 JSONL，已忽略: %s",
            len(nsfw_not_in_jsonl),
            nsfw_not_in_jsonl[:20] + (["..."] if len(nsfw_not_in_jsonl) > 20 else []),
        )

    missing_both = set(jsonl_ids_missing_both_cos_dirs(rows))
    force = set(nsfw_in_jsonl)
    targets = sorted(force | missing_both)
    overlap = force & missing_both

    logging.info(
        "nsfw_in_jsonl=%s missing_both_dirs=%s union=%s overlap=%s",
        len(force),
        len(missing_both),
        len(targets),
        len(overlap),
    )

    client = make_client()
    ok, skip, fail = run_ids(
        client,
        rows,
        targets,
        desc="ernie cos nsfw+missing",
        force_regenerate=force,
    )
    logging.info("done: generated=%s skipped=%s failed=%s", ok, skip, fail)


if __name__ == "__main__":
    main()
