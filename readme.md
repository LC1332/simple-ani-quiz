# 简单的二次元分级测试

基于 `local_data/characters_top15000.jsonl` 与 cos 图（`local_data/z_image_txt2img/{id}.jpg`）的问答站点。

## 结构

- `backend/` — FastAPI：出题、`/api/banner`、`/images/*` 静态图
- `frontend/` — React + Vite + TypeScript

## 本地运行

### 1. 后端

**`ModuleNotFoundError: No module named 'app'`** 是因为在**仓库根目录**执行了 `uvicorn app.main:app`，而 Python 只在当前目录找包；`app` 实际在 `backend/app/`。任选其一即可：

**方式 A（推荐，在仓库根目录）**：设置 `PYTHONPATH` 指向 `backend`，再启动：

```bash
cd /path/to/simple-ani-quiz
source .venv/bin/activate   # 或 backend/.venv
pip install -r backend/requirements.txt
export PYTHONPATH="${PWD}/backend"
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

或使用脚本（等价于上面）：

```bash
chmod +x scripts/dev-backend.sh
./scripts/dev-backend.sh --reload
```

**方式 B**：先进入 `backend` 再启动（此时当前目录即包根，`import app` 正常）：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

确保仓库根目录下存在 `local_data/characters_top15000.jsonl` 与 `local_data/z_image_txt2img/`。

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

开发时 Vite 将 `/api` 与 `/images` 代理到 `http://127.0.0.1:8000`，因此需先启动后端。

可选：设置 `VITE_API_BASE`（例如生产环境完整 API 地址）；默认使用相对路径以配合代理。

## API 摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/banner` | top200 中有 cos 图的角色 id，用于首页 banner |
| GET | `/api/quiz?level=easy\|medium\|hard&n=10` | 返回整套题目 |
| POST | `/api/quiz/submit` | 占位，后续接记分 |
| POST | `/api/feedback` | 501 占位 |
| GET | `/images/cos/{id}.jpg` | cos 图 |
| GET | `/images/portrait/{id}.jpg` | 角色头像（若有） |
