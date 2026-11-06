# 模型权重

[English](README.md)

源码仓库不提交 PTH。两个完整 Windows 版本均附带推理权重：网页工作站将其
放在 Web Data ZIP 中；Revit 安装器自动下载自己的环境分片。用户只需下载
所选版本，无需另一个版本。两者使用同一种向量 Flow Matching 模型，不是
独立 raster 实验中的 DDPM。

## 单独下载推理权重

源码用户可下载 **[flow_matching_best.pth](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/flow_matching_best.pth)**
（193,053,154 字节）到本目录，按
[SHA256-model.txt](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/SHA256-model.txt)
校验：

`11fe79209c433ec189b1d19b8626c20ff7319b71aac79915b54e570e89a3c6cb`

它与完整 Windows 包中的精简 PTH 相同；CLIP 另用
`python scripts/setup_models.py` 下载。完整训练 PTH 不上传，原文件来源及
精简推理文件分别记录在 [`manifest.json`](manifest.json)。

从源码运行时，将兼容权重放到 `checkpoints/flow_matching_best.pth`，或通过
`python infer.py --checkpoint ... --prompt "..."` 指定。完整训练 PTH 和精简
推理 PTH 均可使用，网页服务器也接受模型路径。还需要 CLIP 文本编码器，
具体步骤见 [推理指南](../docs/inference.zh.md)。从头训练不依赖作者权重。

原始训练文件的来源记录保存在 [`manifest.json`](manifest.json)，SHA-256 为：

`a2e67e9c96069847d1a0c64b61fb65536faa54c0245e56364e4aea5d98b57bdd`

## 为什么从 770 MB 变成 193 MB

| 内容 | 原始训练 PTH | 发行版推理 PTH |
| --- | --- | --- |
| 正式推理使用的 `model` 张量 | 192,917,136 字节 | 完全相同 |
| EMA 模型副本 | 192,917,136 字节 | 去掉 |
| 优化器张量 | 383,595,056 字节 | 去掉 |
| 调度器和训练状态 | 保留 | 去掉 |
| 必要模型结构参数 | 保留 | 保留 |
| 序列化文件大小 | **770,009,261 字节** | **193,053,154 字节** |

上面使用十进制 MB，序列化还包含少量文件开销。已逐项比对导出的 345 个模型
张量，数值和数据类型与原 PTH 完全相同。没有量化、剪枝或缩小网络。
正式加载器原本就读取 `model`，导出不会切换 EMA／原始模型的选择。
精简版适合推理，不足以精确恢复原来的训练状态。

源码许可不能直接代替训练数据对权重公开和商用的授权。给权重指定许可前，
需核对实际使用的数据协议及 [第三方声明](../THIRD_PARTY_NOTICES.md)。
