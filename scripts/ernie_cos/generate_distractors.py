from __future__ import annotations

import logging
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ernie_cos.common import (  # noqa: E402
    distractor_ids_for_quiz,
    has_cos_jpg,
    load_all_rows,
    make_client,
    run_ids,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    rows = load_all_rows()
    d = distractor_ids_for_quiz(rows)
    missing = sorted(cid for cid in d if not has_cos_jpg(cid))
    logging.info("distractor pool size=%s need_generate=%s", len(d), len(missing))
    client = make_client()
    ok, skip, fail = run_ids(client, rows, missing, desc="ernie cos distractors")
    logging.info("done: generated=%s skipped=%s failed=%s", ok, skip, fail)


if __name__ == "__main__":
    main()
