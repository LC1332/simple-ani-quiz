# 为top 2600的角色用ernie-image-turbo生成cosplay照片

我正在制作一个通过cos照片来猜是什么角色的应用
这里我的jsonl文件存储了top 2600的角色
这个jsonl在 local_data/characters_top15000.jsonl

我会分成3个级别（1-200，201-800，801-2600）来构造问题
这里的task我们需要先 生成每个角色的照片

# 要求

- 在local_data中新建一个文件夹ernie-image 来存储生成好的cos照片
- 源代码可以在scripts文件夹中 如果你打算有很多文件的话可以在里面新建一个子文件夹
- 建立一个程序依次生成top rank的角色的cos照片
- 照片统一采用768x1376尺寸，用jpg保存
- 我之前试验ernie-image模型有可能生成不是cos照片，prompt需要优化
    - 如果前两个关键字里面没有cosplay，强行把第一个关键字改为 "{原来的第一关键字} cosplay"
- 已经生成过的角色跳过
- 生成顺序（可以写不同的script）
    - 先生成top 10的图
    - 然后生成11-2600的cosplay图
    - 生成1-2600的干扰角色cosplay图
        - 因为我干扰选项的角色也要生成，生成1-200角色对应的 “以prompt作为embedding的K近似的角色id” 中间排名最高的5个干扰角色
        - 注意也是以对应角色的id保存的（这样不会重复生成）
    - 这里注意因为每个角色 以及干扰角色都是唯一id的，所以一定不要重复生成浪费时间
- 生成程序要有tqdm进度显示， top 10 的图的脚本 和后面的可以分离（top 10 跑完我要人工检查）

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