#!/usr/bin/env python3
"""
根据 data/remove_nsfw_list.jsonl 将 cos 图从 z_image_txt2img 移到 z_image_nsfw。
在仓库根目录执行: python scripts/apply_nsfw_removals.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REMOVE_LIST = REPO_ROOT / "data" / "remove_nsfw_list.jsonl"
COS_DIR = REPO_ROOT / "local_data" / "z_image_txt2img"
NSFW_DIR = REPO_ROOT / "local_data" / "z_image_nsfw"


def load_ids(path: Path) -> list[int]:
    ids: list[int] = []
    if not path.is_file():
        print(f"warn: remove list 不存在: {path}", file=sys.stderr)
        return ids
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                ids.append(int(obj["id"]))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                print(f"warn: 跳过无效行: {line[:80]}... ({e})", file=sys.stderr)
    # 去重，保持顺序（后者覆盖无意义，仅保留首次出现顺序）
    seen: set[int] = set()
    unique: list[int] = []
    for i in ids:
        if i in seen:
            continue
        seen.add(i)
        unique.append(i)
    return unique


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply remove_nsfw_list: move jpg to z_image_nsfw")
    parser.add_argument("--dry-run", action="store_true", help="只打印不移动文件")
    args = parser.parse_args()

    ids = load_ids(REMOVE_LIST)
    if not ids:
        print("没有需要处理的 id（列表为空或文件不存在）。")
        return

    NSFW_DIR.mkdir(parents=True, exist_ok=True)

    moved = 0
    skipped = 0
    missing = 0

    for cid in ids:
        src = COS_DIR / f"{cid}.jpg"
        dst = NSFW_DIR / f"{cid}.jpg"
        if dst.is_file():
            if args.dry_run:
                print(f"[skip] {cid}: 已在 z_image_nsfw")
            skipped += 1
            continue
        if src.is_file():
            if args.dry_run:
                print(f"[move] {cid}: txt2img -> nsfw")
            else:
                shutil.move(str(src), str(dst))
            moved += 1
            continue
        print(f"[missing] {cid}: 两处均无 {cid}.jpg", file=sys.stderr)
        missing += 1

    print(f"完成: moved={moved} skipped={skipped} missing={missing} dry_run={args.dry_run}")


if __name__ == "__main__":
    main()
