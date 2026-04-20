#!/usr/bin/env bash
# 从仓库根目录启动 API：把 backend 加入 PYTHONPATH，使 `import app` 可用。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT}/backend"
cd "$ROOT"
exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8010 "$@"
