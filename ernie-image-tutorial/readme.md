参考教程见：`ernie-image-tutorial/tutorial.ipynb`

该 Notebook 参考 `ernie-image-tutorial/reference_proj.ipynb` 的结构，提供：

- 随机从 **top-N**（默认 top2000，可配置）角色中挑选一个 `diffusion_prompt` 生成 cosplay 图
- 支持按中文名 / 日文名 / 作品名进行模糊搜索，并生成**第一个命中**的角色
- Gradio Demo（随机 / 搜索 两个 Tab）

示例素材图在：`ernie-image-tutorial/samples/`

## 数据集（AIStudio）

数据集已上传到 AIStudio：`LC1332/anime-character-prompt-15k`

参考下列方式获取：

```bash
# 首先请先安装 aistudio-sdk
pip install --upgrade aistudio-sdk

# 下载整个数据集到 ./data（可自行修改 local_dir）
aistudio download --dataset LC1332/anime-character-prompt-15k --local_dir ./data

# 下载单个文件示例：README.md
aistudio download README.md --dataset LC1332/anime-character-prompt-15k --local_dir ./data
```

## 批量生成（脚本）

更完整的批量生成脚本见：`scripts/ernie_cos/`