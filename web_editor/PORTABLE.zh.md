# Text2Floorplan — Windows 网页版

[English](README.md)

从文字生成户型，在浏览器里编辑联动的二维平面和三维模型。完整包自带 Python、
PyTorch、CLIP 和训练权重，无需另外安装 Python、Conda、Revit 或解压软件。
生成使用本地 Flow Matching，无需 LLM、API Key 或云端推理服务。

## 选择使用版本

本包是独立 **网页工作站**，启动器 `Start-Text2Floorplan.cmd` 已放在 Web 主 ZIP
中。无需下载安装 `text2floorplan_revit-Setup.exe` 或 `environment.7z.*`，这些
属于独立的 Revit 插件；只用插件的用户只需下载其安装 EXE。两版可同时使用，
但目前各自保留运行环境和模型副本。

## 启动

1. 下载的是 **完整离线 ZIP**：把整个 ZIP 解压到可写的本地文件夹，首次启动前
   选好最终存放位置。
2. 下载的是 **分文件发行版**：将 `Text2Floorplan-Web-Windows.zip` 和
   **全部** `Text2Floorplan-Web-Data-*.zip` 下载到同一位置。只解压主 ZIP，
   数据 ZIP 留在原下载位置，不用移动，也不用逐一解压数据 ZIP。
3. 进入解压后的 `Text2Floorplan`，双击 **`Start-Text2Floorplan.cmd`**。
   首次会校验并展开运行环境、检查模型，再自动打开默认浏览器，可能需要数分钟。
   以后启动复用已准备的环境。

仅下载需要联网，推理在本机离线完成。使用时保留命令窗口，关闭窗口或 Ctrl+C
会停止服务。程序自动选择空闲的本机端口。不要直接双击 `index.html`，推理和编辑
需要本地 Python 后端。首次打开页面为空白，可生成、导入样例或打开已有 JSON。
默认英文，可在语言菜单切换中文。

## 提示词

```text
A small 2-bedroom apartment with 1 bathroom and 1 balcony.
A 3-bedroom apartment with 2 bathrooms and 1 balcony.
A large 4-bedroom apartment with 2 bathrooms and 2 balconies.
```

可改大小、卧室数、卫生间数和阳台数。中户型省略大小词，不要输入 `none`。
每套户型包含一个客厅和一个厨房。

## 主要功能

- 二维／三维联动、平移、缩放、旋转观察和俯视。
- 选墙即显示两端圆点和中心方点；拖端点独立修改一端，拖中心移动整段及门窗。
- 节点、交点及墙线吸附，Alt 临时关闭吸附。
- 拖门窗边调整尺寸，拖中心换墙并自动转向；门可翻转开门方向、交换铰链侧。
  放不下或与其他门窗冲突时拒绝修改，原模型保留。
- 修改墙高、墙厚、门窗宽高、窗台高及离地高度。
- 按当前封闭墙线重算房间及总净面积，未闭合空间明确标注；阳台保留开放栏杆。
- 撤销／重做、导入／导出可编辑 JSON、导出三维 PNG。

刷新或关闭网页前请先 **保存模型**，未保存的编辑不会自动保留。该版本输出
可编辑 JSON 和预览，不直接创建 Revit 构件或 RVT 文件。

不打开网页也可生成：首次准备好运行环境后，在程序目录运行
`.\runtime\python.exe -B infer.py --prompt "..."`。随包的 `docs/inference.zh.md`
介绍 PNG／JSON 输出和模型选项。

## 要求与排查

需要 Windows x64 和支持 WebGL 的桌面浏览器。支持 CPU 推理；兼容的 NVIDIA
显卡和驱动可自动加速，显卡不可用时回退 CPU，速度取决于设备。

包中包含数 GB 的运行库及模型，需要同时容纳下载的 ZIP 和解压内容。首次启动
会计算展开所需空间，不足时提示。准备成功后可将数据 ZIP 移到备份盘；若要
准备另一份程序，仍需保留这些数据包。不要移动已经初始化的程序文件夹；
需要换位置时从原 ZIP 重新解压，并另行保存已有模型。

数据 ZIP 缺失或校验失败时，重新下载对应文件。如果启动失败，请保留命令窗口的
报错并参考 `web_editor/README.zh.md` 中的编辑器说明。需要强制 CPU 时，先在 CMD 中
运行 `set TEXT2REVIT_DEVICE=cpu`，再启动。该版本不会注册 Revit 插件或 Windows
服务，也不需要管理员安装；删除解压文件夹即可移除，已下载的模型 JSON 单独保留。

## 许可

Copyright (c) 2026 Simon H. 项目原创内容采用 MIT License (`LICENSE`)。
运行库、CLIP 和数据集保留各自条款，见 `THIRD_PARTY_NOTICES.md` 中的第三方声明。
原始数据集及训练数据未打包。
