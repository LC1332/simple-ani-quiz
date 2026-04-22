# NSFW的小规模标记

这里我发现有些角色的cos生成图出现了裸露 比如 96815

我想到了两条办法在不运行昂贵模型的情况下寻找潜在裸露照片的方法

- 通过prompt里面出现 "ge breast" 的 （包括huge/large breasts） 一共80张左右的图
- 如果我标记了1张nsfw的图，那么这张图的k近邻（在local_data/characters_top15000.jsonl中有两个k近邻字段）都有可能是潜在candidate

我需要
- 实现一个程序 能够显示所有的candidate图片 并且让我标记哪些是nsfw的
    - 一页显示多个，然后支持刷新翻页（注意标记后candidate list是会更新的）
- 在我标记之后，会产生一个 data/remove_nsfw_list.{合适的后缀名} 的文件 记录所有的nsfw图片清单
- 对应的图片会从local_data/z_image_txt2image中移动到 local_data/z_image_nsfw中
- 标记一张图片的时候 对应这张图片的近邻也会加入到candidate中
    - 可以考虑维护一个队列保住candidate的加入顺序，这样看起来省事儿一些
- 因为我之后remove list 会同步到git 这样的话 我需要一个script，能够一键确认local_data/z_image_txt2img中的对应图片都移动到nsfw