# Text2Floorplan v1.1.0 — Windows 网页版与 Revit 插件版

使用 Flow Matching 从文字直接生成可编辑户型图和三维模型，**无需 LLM、
API Key 或云端推理服务**。完整 Windows 版自带 Python、PyTorch、CLIP 和
训练权重，无需另外配置环境。

## 选择使用版本

网页工作站和 Revit 插件独立使用，只需下载需要的一套，不共用启动器，也不要求
安装另一版本。

| 版本 | 下载内容 | 启动方式 |
| --- | --- | --- |
| 网页工作站，无需 Revit | Web 主 ZIP 和全部四个 Web Data ZIP | 只解压主 ZIP，运行其中的 `Start-Text2Floorplan.cmd` |
| Revit 插件 | `text2floorplan_revit-Setup.exe`，依赖由安装器自动下载 | 安装后从 Revit 工具栏启动 |

插件用户不需要 Web ZIP；网页用户不需要 Revit 安装器或 `environment.7z.*`。
两版都使用时，目前各自保留运行环境和模型副本。

## 下载与启动

将 `Text2Floorplan-Web-Windows.zip` 和全部编号的
`Text2Floorplan-Web-Data-*.zip` 下载到同一位置，只解压主 ZIP。
进入解压出的 `Text2Floorplan`，双击 `Start-Text2Floorplan.cmd`。
首次自动校验并解压环境，成功前请让数据 ZIP 保留在原下载位置。
下载校验值见 `SHA256-web.txt`。

完整离线 ZIP 包含同一套文件，但超过发行平台的单文件限制，需要另行提供下载地址。
编号数据 ZIP 是独立的普通 ZIP，不是 `.zip.001` 切片，用户不需要安装 7-Zip。

## 功能

- 默认英文，可选中文；支持大小及房间数量提示词。
- 墙端点和整段独立移动、节点吸附、净面积重算。
- 门窗尺寸编辑、跨墙移动并转向，门的开门方向和铰链侧翻转。
- 二维／三维联动、开放阳台栏杆、撤销／重做、JSON 保存及三维 PNG 导出。
- CPU 可用，兼容的 NVIDIA 显卡自动加速，并保留 CPU 回退。

仅提供 Windows x64。程序在本机浏览器运行，不是公开托管的网站，也不是双击一个
HTML 就能独立推理。模型在用户电脑上运行。原生 Revit 集成单独提供为 Text2Floorplan Revit 插件版。

项目原创代码现采用 MIT License，Copyright (c) 2026 Simon H.，第三方许可随包保留。
运行环境在开发电脑中验证，全新外部电脑的实际试用仍待完成。

## Revit 插件版

原生集成现称 **Text2Floorplan Revit**。用户下载 `text2floorplan_revit-Setup.exe`，
安装器自动获取配套的 `environment.7z.*`；独立卸载工具为
`text2floorplan_revit-Uninstall.exe`，校验文件为 `SHA256-revit.txt`。
Revit 2020–2026 DLL 已重新编译，保留原注册身份和数据位置以兼容旧安装。
仓库 README 同时保留网页版和 Revit 原生示例图。

## 源码直接推理

仓库新增 `infer.py`，直接输入 prompt 生成 PNG／JSON，复用正式后端。
准备好依赖、CLIP 和兼容权重后运行：

```powershell
python infer.py --prompt "A 3-bedroom apartment with 2 bathrooms and 1 balcony."
```

源码用户可直接下载本 Release 的 **[flow_matching_best.pth](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/flow_matching_best.pth)**
（193 MB）到 `checkpoints/`，校验值见 `SHA256-model.txt`。完整 Windows 版本
已附带该权重，用户无需重复下载。原始完整训练 PTH 不分发。

JSON 可在网页工作站打开并编辑。完整和精简 PTH 均可使用；精简版去掉训练状态，
不量化、不剪枝。源码用法见 `docs/inference.md` 和 `docs/inference.zh.md`。
