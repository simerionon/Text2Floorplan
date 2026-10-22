# Text2Floorplan v1.1.0 — Windows browser and Revit editions

Generate apartment floor plans from text and edit linked 2D and 3D models locally,
without Revit. This release includes the Python runtime, PyTorch, CLIP and the
trained checkpoint; no environment setup is required.

## Download and start

Download `Text2Floorplan-Web-Windows.zip` and every numbered
`Text2Floorplan-Web-Data-*.zip` asset into one folder. Extract only the main ZIP,
open the resulting `Text2Floorplan` folder and double-click
`Start-Text2Floorplan.cmd`. First launch checks and extracts the data automatically.
Keep all data ZIPs in the original download folder until preparation finishes.
`SHA256-web.txt` lists the download checksums.

A complete offline ZIP contains the same files in one download. It exceeds the
per-file release asset limit and is provided separately when an alternative
download location is available. The numbered data ZIPs are ordinary independent
ZIPs, not `.zip.001` archive fragments; users do not need 7-Zip.

## Features

- English and optional Chinese UI; supported size and room-count prompts.
- Independent wall endpoint/segment movement, snapping and recalculated net areas.
- Hosted door/window resizing and movement between walls, automatic orientation,
  door swing reversal and hinge-side changes.
- Linked 2D/3D views, open balcony railings, undo/redo, saved JSON and 3D PNG export.
- CPU inference with compatible NVIDIA GPU acceleration and CPU fallback.

Windows x64 only. This is a local browser application, not a hosted public site
or a single HTML file that runs inference by itself. Models stay on the user's
computer. Native Revit support remains a separate Text2Floorplan Revit edition.

The original project code is now licensed under MIT, copyright 2026 Simon H.
Third-party licenses remain in the package. The prepared runtime is checked on
the development machine; a clean external-PC trial remains to be completed.

## Revit edition

The native integration is now named **Text2Floorplan Revit**. Download
`text2floorplan_revit-Setup.exe`; it automatically retrieves the accompanying
`environment.7z.*` assets. `text2floorplan_revit-Uninstall.exe` provides standalone
removal. `SHA256-revit.txt` records its checksums. Revit 2020–2026 DLLs were rebuilt;
existing registration identities and local data paths are retained for compatibility.
Both browser and native Revit example images remain in the repository README.
