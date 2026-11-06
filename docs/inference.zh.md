# 文字生成户型：直接运行推理

[English](inference.md)

源码仓库已包含完整的正式推理流程，无需 Revit、浏览器、LLM、API Key 或云端
推理服务。CLIP 编码支持的英文提示词，向量 Flow Matching 模型生成房间布局，
再完成几何修复、门窗布置和面积检查。当前正式模型是 Flow Matching，
与工作区中独立的 raster FM／DDPM 实验不是同一套模型。

## 首次准备

使用 Python 环境；本地已验证 Windows x64、Python 3.14 和 PyTorch 2.11。
从源码仓库根目录运行：

```powershell
python -m pip install -r requirements.txt
python scripts/setup_models.py
```

第二条命令下载 `openai/clip-vit-large-patch14` 到 `models/clip/`。
从 Release 下载单独的 **[193 MB PTH](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/flow_matching_best.pth)**，
校验值见 [SHA256-model.txt](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/SHA256-model.txt)。
将兼容权重放到 `checkpoints/flow_matching_best.pth`，或通过 `--checkpoint`
指定。原始完整训练 PTH 和精简推理 PTH 均可使用。已准备好的 Windows 程序
在 `models/` 中包含 Flow 权重及 `clip/`，也可直接指定其中的路径。
权重文件不提交到 Git，见 [权重说明](../checkpoints/README.zh.md)。

首次下载依赖和模型需要联网，之后推理在本地离线运行。只想使用应用、不想
配置 Python 的用户，选择完整的 [Windows 版本](../README.zh.md#选择使用版本)。

本次更新的网页便携包也附带命令行入口。先用正常启动器完成一次环境准备，
之后可在解压出的 `Text2Floorplan` 目录运行，直接使用自带 Python 和模型：

```powershell
.\runtime\python.exe -B infer.py --prompt "A 3-bedroom apartment with 2 bathrooms and 1 balcony."
```

命令行生成时无需保持网页服务器运行。

## 生成平面图和可编辑 JSON

```powershell
python infer.py --prompt "A 3-bedroom apartment with 2 bathrooms and 1 balcony."
```

指定模型路径、强制 CPU、设置初始种子及输出目录：

```powershell
python infer.py --prompt "A small 2-bedroom apartment with 1 bathroom and 1 balcony." --checkpoint "C:/Models/flow_matching_best.pth" --clip-dir "C:/Models/clip" --device cpu --seed 42 --output-dir outputs/my_plans
```

默认 `--device auto`，兼容的 NVIDIA 显卡自动加速，并保留 CPU 回退；
`--device cpu` 强制使用 CPU。`--language zh` 只切换进度提示，prompt 仍用英文。
中户型省略大小词，只修改大小、卧室数、卫生间数和阳台数；每套户型含一个
客厅和一个厨房。

默认在 `outputs/inference/` 输出带唯一时间戳的文件：

- `floorplan_年月日_时分秒_微秒.png`：带房间及总面积的二维预览。
- 同名 `.json`：房间、墙体、门窗、阳台栏杆、物理尺度、prompt、最终种子和
  净面积。可在网页工作站点击 **Open JSON／打开 JSON**，进行二维／三维联动编辑。

该入口复用网页工作站和 Revit 插件的正式后端，包含不合格布局重试，以及
厨房／卫生间最低面积检查。`--seed` 是首次尝试的种子，布局被拒绝后会换种子
重试；最终种子保存在 JSON 中。推理默认 200 个求解步骤，不需要训练 GT、
预先生成的 mask、原始数据集或训练进程，但需要仓库中小型 `data/` 先验及配置。

CLI 输出几何及预览，不直接生成 RVT；原生 Revit 模型通过独立插件创建。
当前插件尚未提供任意编辑后 JSON 的工具栏导入命令。

## 推理代码位置

| 文件 | 作用 |
| --- | --- |
| `infer.py` | 用户命令行入口，选择模型路径、设备和输出位置 |
| `backend_cli.py` | 共用正式后端，包含检查、重试、预览和结构化 JSON |
| `pipeline_generate.py` | 提示词／拓扑采样、CLIP、模型加载、几何恢复和门窗布置 |
| `inference_runtime.py`、`flow_solver.py` | 独立推理执行及 Heun 求解 |
| `model.py` | 向量 Flow Matching Transformer 结构 |
| `geometry_cleanup.py`、`plan_postprocess.py` | 几何修复 |
| `door_window_rules.py`、`revit_geometry.py`、`plan_quality.py` | 门窗、物理尺寸和净面积检查 |

原有 `pipeline_generate.py` 命令继续保留，支持 `--steps`、`--seed`、
`--checkpoint`、`--clip-dir` 和 `--output-dir`，输出管线中间元数据。
需要网页可编辑格式时使用 `infer.py`。程序集成可调用
`backend_cli.py --request request.json --response plan.json`，请求 JSON 例如
`{"prompt": "A 3-bedroom apartment with 2 bathrooms and 1 balcony.", "seed": 42,
"language": "zh"}`，其中 seed 可省略。

## 为什么 770 MB 变成 193 MB

原始 PTH 为 **770,009,261 字节**，发行版为 **193,053,154 字节**。
原文件包含模型参数、完整 EMA 模型副本、优化器动量、学习率调度及训练状态；
推理版只保留 `model` 和必要的模型结构参数。

已将发行版的 **345 个张量**逐项与原 PTH 的 `model` 比较，数值和数据类型完全一致。
没有量化、剪枝或缩小网络。正式加载器原本就使用 `model`，而不是 `ema_model`，
导出没有改变这一选择。精简版可以直接推理，但不具备精确恢复训练所需的完整状态。

训练数据和第三方内容的授权与源码许可分别处理，见
[第三方声明](../THIRD_PARTY_NOTICES.md)。
