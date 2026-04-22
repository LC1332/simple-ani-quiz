# TODO List

- 将重新生成Cos图 的栏目调整为默认展开，去掉（预留）
- API Token这里的括号说明 使用aistudio 的token 不输入的情况下 默认使用项目后台.env中的api
- 确保生成的结果是连接上的
- 默认尺寸调整为 宽768 高1376。
- 其他的尺寸都对应上ernie-image 支持的尺寸
- 有时候生成会报错 

比如 openai.BadRequestError: Error code: 400 - {'logId': 'bb65e230e502f463d5f16993d4421d4f', 'errorCode': 40000, 'errorMsg': '内容不合规'}

把这个错误返回给前端

# 例子

api_key我已经放在了.env中，为AISTUDIO_API_KEY字段

```python
import base64
from openai import OpenAI

client = OpenAI(
    api_key={api_key},
    base_url="https://aistudio.baidu.com/llm/lmapi/v3",
)

img = client.images.generate(
    model="ernie-image-turbo",
    prompt="一只可爱的猫咪坐在窗台上",
    n=1,                            # 可选：1、2、3、4
    response_format="url",     # 可选：b64_json、url
    size="1024x1024",               # 可选：1024x1024、1376x768、1264x848、1200x896、896x1200、848x1264、768x1376
    extra_body={"seed": 42, "use_pe": True, "num_inference_steps": 8, "guidance_scale": 1.0}
)

image_bytes = base64.b64decode(img.data[0].b64_json)
with open("output.png", "wb") as f:
    f.write(image_bytes)
```