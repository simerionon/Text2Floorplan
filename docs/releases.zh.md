# Windows 发行文件

[English](releases.md)

仓库：`Simon777hh/text2floorplan`，本次发布标签：**`v1.1.0`**。

## 网页版

一并上传以下文件：

- `Text2Floorplan-Web-Windows.zip`
- `Text2Floorplan-Web-Data-1.zip`
- `Text2Floorplan-Web-Data-2.zip`
- `Text2Floorplan-Web-Data-3.zip`
- `Text2Floorplan-Web-Data-4.zip`
- `SHA256-web.txt`

用户把五个 ZIP 下载到同一位置，只解压主 ZIP，双击
`Start-Text2Floorplan.cmd`，启动器自动准备环境。这些数据 ZIP 是独立的普通 ZIP。
可选的 `Text2Floorplan-Web-Windows-Offline.zip` 将同样内容放在一个完整下载中，
但超过平台的 2 GiB 单文件限制，需要另行托管；上述文件已提供全部离线使用能力，
无需额外下载那个完整 ZIP。

## Revit 插件版

在 **同一个 `v1.1.0` Release** 一并上传：

- `text2floorplan_revit-Setup.exe`
- `text2floorplan_revit-Uninstall.exe`
- Revit 打包程序输出的全部 `environment.7z.*`
- `SHA256-revit.txt`

用户只手动下载安装 EXE，安装器自动下载数据。仓库名、标签和数据文件名须与
安装器内置地址一致，变更时用正确的 `--online-release-url` 重新打包。
显示名称为 **Text2Floorplan Revit**，内部程序集、注册信息和安装位置保留旧命名，
用来兼容已有安装。

## 源码与许可

仓库根目录是包含主 README 的源码目录。运行环境、训练权重、安装包和生成结果
不进入普通 Git；完整 Windows 发行包自带推理模型。平台自动生成的 **Source code ZIP**
只是源码，不能替代准备好的应用包。

项目原创内容采用 MIT License，Copyright (c) 2026 Simon H.。两个发行版均保留
第三方声明和许可。构建命令见 [开发指南](development.md)，验证范围与局限见
[检查记录](audit.md)。
