# Windows release files

[中文](releases.zh.md)

Repository: `Simon777hh/text2floorplan` · Release tag: **`v1.1.0`**.

## Browser edition

Upload these assets together:

- `Text2Floorplan-Web-Windows.zip`
- `Text2Floorplan-Web-Data-1.zip`
- `Text2Floorplan-Web-Data-2.zip`
- `Text2Floorplan-Web-Data-3.zip`
- `Text2Floorplan-Web-Data-4.zip`
- `SHA256-web.txt`

Users download all five ZIPs to the same folder, extract only the main ZIP and
double-click `Start-Text2Floorplan.cmd`. All data parts are ordinary ZIP files;
the launcher prepares the runtime automatically. The optional complete
`Text2Floorplan-Web-Windows-Offline.zip` contains the same files but exceeds
the platform's 2 GiB asset limit. Host that single ZIP elsewhere if desired;
the assets above provide the complete offline functionality without it.

## Revit edition

Upload these assets together to **the same `v1.1.0` release**:

- `text2floorplan_revit-Setup.exe`
- `text2floorplan_revit-Uninstall.exe`
- Every `environment.7z.*` file produced by the Revit builder
- `SHA256-revit.txt`

Users download only the setup EXE; it retrieves its data files automatically.
Keep the repository, tag and data filenames unchanged because the URLs are
embedded in the installer. Rebuild with the appropriate `--online-release-url`
if any of them changes. The new display name is **Text2Floorplan Revit**;
legacy internal assembly, registration and installation paths are retained
to support existing installations.

## Source and licensing

The repository root is the source checkout containing the main README. Runtime
downloads, trained weights, release binaries and generated outputs are excluded
from ordinary Git. The complete Windows releases supply the inference models.
Do not substitute the platform's automatic **Source code ZIP** for a prepared
application download.

Original project material is licensed under MIT, copyright 2026 Simon H.
Third-party notices and licenses accompany both distributions. See
[the development guide](development.md) for build commands and
[the audit](audit.md) for validation scope and remaining limitations.
