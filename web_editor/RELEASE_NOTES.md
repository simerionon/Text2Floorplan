# Text2Floorplan v1.1.0 — Windows browser and Revit editions

Generate editable apartment floor plans and 3D models directly from text using
Flow Matching — **no LLM, API key or cloud inference service required**.
The complete Windows editions include Python, PyTorch, CLIP and the trained
checkpoint; no separate environment setup is required.

## Choose your edition

The browser workstation and Revit plug-in are independent. Download only the
edition you need; they do not share a launcher or require each other's installation.

| Edition | Download | Launch |
| --- | --- | --- |
| Browser workstation — no Revit required | Main Web ZIP + all four Web Data ZIPs | Extract the main ZIP and run its `Start-Text2Floorplan.cmd` |
| Revit plug-in | `text2floorplan_revit-Setup.exe`; dependencies download automatically | Install, then use the Revit ribbon |

Revit users do not need Web ZIPs. Browser users do not need the Revit setup EXE
or `environment.7z.*`. Installing both currently keeps two runtime/model copies.

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

## Source inference

The repository includes `infer.py`, a direct prompt-to-PNG/JSON entry that reuses
the production backend. After preparing dependencies, CLIP and compatible weights:

```powershell
python infer.py --prompt "A 3-bedroom apartment with 2 bathrooms and 1 balcony."
```

Source users can download **[flow_matching_best.pth](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/flow_matching_best.pth)**
(193 MB) directly from this release and place it in `checkpoints/`. Its download
checksum is in `SHA256-model.txt`. Complete Windows editions already include it;
their users do not need this separate download. The original full training PTH
is not distributed.

The JSON opens in the browser workstation for editing. Both full and compact
PTH files work; the compact checkpoint removes training state without quantizing
or pruning model tensors. Source instructions are in `docs/inference.md` and
`docs/inference.zh.md`.
