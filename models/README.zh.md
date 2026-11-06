# 本地推理模型

[English](README.md)

网页工作站、命令行推理和 Revit 插件共用同一种向量 Flow Matching 权重及
CLIP 文本编码器，无需 LLM、外部推理 API 或 API Key。两个完整 Windows 版本
各自附带模型，运行环境和模型副本独立。

从源码使用时，在仓库根目录运行 `python scripts/setup_models.py`，将
`openai/clip-vit-large-patch14` 下载到 `models/clip/`。首次下载需要联网，
之后推理离线读取本地编码器。下载文件由 Git 忽略。

源码的 Flow 权重放在 `checkpoints/flow_matching_best.pth`，或使用
`--checkpoint` 指定。完整 Windows 程序将精简权重与 `clip/` 一起放在各自的
`models/` 文件夹，路径可传给 [命令行](../docs/inference.zh.md) 或
[网页服务器](../web_editor/README.zh.md)。

`models/` 保存模型；训练阶段的 `data/clip/` 是预计算文本特征，不能替代
推理所需的文本编码器。模型下载和生成的特征均不进入源码仓库。
参阅 [权重说明](../checkpoints/README.zh.md) 和
[第三方声明](../THIRD_PARTY_NOTICES.md)。
