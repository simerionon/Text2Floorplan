# Text2Floorplan — Windows browser edition

[中文](README.zh.md)

Generate apartment layouts from text and edit the linked 2D plan and 3D model
in your browser. The complete package includes Python, PyTorch, CLIP and the
trained model. No Python, Conda, Revit or separate archive tool is required.
Generation is local Flow Matching; no LLM, API key or cloud inference service
is needed.

## Choose your edition

This package is the independent **browser workstation**. Its launcher is
`Start-Text2Floorplan.cmd`, included in the main Web ZIP. You do not need
`text2floorplan_revit-Setup.exe` or `environment.7z.*`. Those belong to the
separate Revit plug-in, whose users download only its setup EXE. The two editions
can coexist, but currently keep separate runtime/model copies.

## Start

1. For the **complete offline ZIP**, extract the entire ZIP to a writable local
   folder. Choose its final location before the first launch.
2. For the **release assets**, download `Text2Floorplan-Web-Windows.zip` and
   **every** `Text2Floorplan-Web-Data-*.zip` into the same folder. Extract only
   `Text2Floorplan-Web-Windows.zip`. Leave the data ZIPs in the original
   download folder; there is no need to move, open or extract each data ZIP.
3. Open the extracted `Text2Floorplan` folder and double-click
   **`Start-Text2Floorplan.cmd`**. First launch verifies and extracts the runtime,
   checks the models, then opens your default browser. This can take several
   minutes; subsequent launches reuse the prepared runtime.

Internet access is needed only to download the package. Inference runs locally.
Keep the console open while editing; Ctrl+C or closing it stops the local server.
The server selects a free localhost port automatically. Do not double-click
`index.html`: the local Python backend is required for inference and editing.

Use **Generate layout** after entering a prompt, **Import sample** for an
immediate editing example, or **Open JSON** to resume a saved model. The page
starts blank. English is the default; Chinese is available in the language menu.

## Supported prompts

```text
A small 2-bedroom apartment with 1 bathroom and 1 balcony.
A 3-bedroom apartment with 2 bathrooms and 1 balcony.
A large 4-bedroom apartment with 2 bathrooms and 2 balconies.
```

Change the size, bedrooms, bathrooms and balconies. Omit the size word for medium;
do not type `none`. Each apartment includes one living room and one kitchen.

## Editing

- Linked 2D and 3D views, pan/zoom, orbit and top view.
- Select a wall to show both endpoint circles and a center square: move one
  endpoint independently, or translate the whole segment with its openings.
- Node, intersection and wall-line snapping; hold Alt to bypass snapping.
- Resize door/window edges; move the center to another wall to snap and turn.
  Doors can flip their swing direction and swap hinge sides. Invalid placements
  are rejected without losing the model.
- Edit wall heights/thicknesses, door/window widths/heights and sill/base heights.
- Recalculate room and total net areas from the current enclosed walls. Open
  spaces are labelled rather than assigned invented areas. Balconies stay open
  with railings.
- Undo/redo, JSON import/export and 3D PNG export.

**Save model** downloads an editable JSON. Unsaved edits are lost when the page
is refreshed or closed. The JSON is compatible with the existing schema; this
edition does not create native Revit elements or RVT files.

For generation without opening the browser, prepare the runtime once and use
`.\runtime\python.exe -B infer.py --prompt "..."` from the application folder.
The included `docs/inference.md` explains PNG/JSON outputs and model options.

## Requirements and troubleshooting

Windows x64 and a current desktop browser with WebGL are required. CPU inference
is supported; a compatible NVIDIA GPU and driver are used automatically, with
CPU fallback if GPU inference cannot run. Speed depends on the device.

The archive includes several GB of runtime libraries and model weights. Keep
enough free space for both the downloaded ZIPs and the extracted files. First
launch calculates the extraction requirement and reports insufficient space.
After preparation succeeds, the numbered data ZIPs can be moved to backup storage;
keep them if you want to prepare another copy of the application. Choose the
final location before first launch; to move an initialized copy, extract a fresh
copy and keep your saved models separately.

If a data archive is missing or its checksum differs, download that file again.
If launch fails, keep the console error and consult the editor guide in `web_editor/README.md`.
For an environment without a usable CUDA driver, launch from a terminal with
`set TEXT2REVIT_DEVICE=cpu` before running the CMD file. No Revit registration,
Windows service or administrator installation is performed. Delete the extracted
folder to remove this edition; saved models in your Downloads remain separate.

## License

Copyright (c) 2026 Simon H. Original project material is under the MIT License (`LICENSE`).
Third-party runtime components, CLIP and datasets retain their own terms; see
`THIRD_PARTY_NOTICES.md`. Raw/training datasets are not bundled.
