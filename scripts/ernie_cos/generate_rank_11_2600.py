from __future__ import annotations

import logging
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ernie_cos.common import (  # noqa: E402
    make_client,
    rows_ranked_1_2600,
    load_all_rows,
    run_ids,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main() -> None:
    rows = load_all_rows()
    ranked = rows_ranked_1_2600(rows)
    ids_11_2600 = [cid for cid, row in ranked if int(row["rank"]) >= 11]
    client = make_client()
    ok, skip, fail = run_ids(client, rows, ids_11_2600, desc="ernie cos rank 11-2600")
    logging.info("done: generated=%s skipped=%s failed=%s", ok, skip, fail)


if __name__ == "__main__":
    main()
