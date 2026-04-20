# 准备simple-ani-quiz的local_data

我准备制作一个新的项目，会用到本项目的数据。

我需要把这个项目中的部分数据整理到 local_data/simple-ani-quiz 中

并且最终压缩为一个压缩包

我需要以下数据

## top15000角色的抽象数据

定义最近邻的K = 8

- 以hugging face上比较支持的jsonl文件保存
- 需要的字段包括
    - 角色的id
    - 角色的中文角色名
    - 角色的日文角色名
    - 角色参演的主要剧目（以角色为主演的某一部剧）
    - 角色的生平（summary）
    - 角色的生成prompt
    - 角色的top rank（收藏数排序的rank）
    - image_url(在bgm网站的url，保存一张最大的就可以)
    - 以角色图片作为embedding的K近似的角色id
    - 以prompt作为embedding的K近似的角色id

实际上这些信息应该都可以在local_data/bangumi/characters_ranked.json中找到

额外保存一个10条的sample.jsonl来给我进行检查

## top 15000 角色的cosplay图

把outputs/z_image_turbo/txt2img 中的图片
压缩到 local_data/simple-ani-quiz中


## top 2600 角色的角色图

保存到 local_data/simple-ani-quiz的一个子文件夹中
以jpg格式 这样稍微小一点

## top-k 

我需要存储“这个角色”和哪些角色长得最像 这里我准备使用两种embedding
一种是角色自己角色图的图片embedding 

一种是角色自己prompt的embedding

对于这两种embedding，各自建库，然后对自己库搜索（K+1）的最近邻（去掉第一个自己本身）

然后这里的两种各自的top-k（id形式）也要保存在jsonl中

因为我需要用“最像”的角色 去做 cos测试的干扰项

- 不要重新抽取embedding 应该是已经预存了

# reference and protocol

- 对于数据的存储结构你可以在 information/data_save_structure.md中找到
- 其实当前需求文件已经说得很清楚了 就是embedding的你可能要找一下预存的位置