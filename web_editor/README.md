# Text2Floorplan — local browser editor

[中文](README.zh.md)

Generate an apartment with the existing local model, edit its 2D room corners,
and inspect the linked 3D walls, doors, windows and balcony railings. Revit is
not required to use the editor. English is the default; select Chinese in the
top-right language menu. Prompts use the same supported English format.

This is the independent **browser workstation**, with its own launcher and
runtime. Revit users instead install `text2floorplan_revit-Setup.exe`; neither
edition requires the other. Generation uses local CLIP and Flow Matching, with
no LLM, API key or cloud inference service.

## Complete Windows edition

The release includes a self-contained browser edition with Python, PyTorch,
CLIP and trained weights. Follow the [Windows package guide](PORTABLE.md):
download the main ZIP and all numbered data ZIPs together, extract the main ZIP
and double-click `Start-Text2Floorplan.cmd`. The launcher chooses a free local
port; no Revit or Python installation is required. A complete offline ZIP is
also built for distribution through a separate download host.

## Run from source

On Windows, double-click **`web_editor/Start-Editor.cmd`**. Keep its console
window open while editing. Close that window, or press Ctrl+C, to stop the
local process. If the default port is occupied, pass `--port 8768` when starting
from a terminal.

The launcher checks `TEXT2REVIT_PYTHON`, a local Conda environment named
`Text2Revit`, an installed Revit-edition runtime, then `python` on PATH. This
source launcher reuses an existing Python environment and does not install
dependencies. The complete Windows edition above includes its own runtime.

Alternatively, from the repository root:

```powershell
python -m pip install -r requirements.txt
python scripts/setup_models.py
python -m web_editor.server --open
```

Provide a compatible full or inference-only PTH; see the
[inference guide](../docs/inference.md) for model paths and CPU selection.
The same guide documents `python infer.py --prompt "..."` for generation without
opening the workstation; its output JSON can then be opened here.

The English page is `http://127.0.0.1:8765/en`; the Chinese page is
`http://127.0.0.1:8765/zh`. `/` also opens English. The language menu changes
the page URL while preserving the current model. Use `--language zh --open`
to open Chinese directly.

The page starts with an empty workspace and an empty prompt. Generate a layout
or open a saved JSON model to begin. **Import sample** explicitly imports the
bundled example for editing without loading the trained model. NumPy and Shapely are needed for
editing; inference also needs the dependencies in `requirements.txt` and the
trained checkpoint/CLIP encoder described in the main README.

If an existing Text2Revit installation contains local models, the editor can
reuse them. Explicit model and inference-Python paths are supported:

```powershell
python -m web_editor.server --open --python C:/Python/python.exe --checkpoint C:/Models/flow_matching_best.pth --clip-dir C:/Models/clip
```

## Prompt format

`A (large / small / none = default) n-bedroom apartment with n bathrooms and n balconies.`

Replace each `n` with the desired count. Use `small` or `large`; omit the size
word for the default medium apartment. `none` explains an omitted option and
must not be typed into the actual prompt. The page offers three clickable examples:

- `A small 2-bedroom apartment with 1 bathroom and 1 balcony.`
- `A 3-bedroom apartment with 2 bathrooms and 1 balcony.`
- `A large 4-bedroom apartment with 2 bathrooms and 2 balconies.`

An example fills the prompt without generating. Click **Generate layout** or
press Enter in the prompt field to start inference.

## Edit

- Select a room in the plan to reveal its corner handles. Drag a handle to
  reshape it; X follows connected vertical room boundaries and Y follows
  horizontal boundaries, including shared runs and T junctions. Dragging snaps to 100 mm.
  Focus a corner and use arrow keys for 100 mm increments.
- Selected rooms also expose edge handles and a center. Drag an edge to move
  that boundary perpendicularly; drag the center to translate the complete
  room while maintaining its shape. Room boundaries stay connected to adjacent
  room boundaries. For a closed room, an explicit room edit also transforms
  its physical boundary wall nodes. Open, merged, split or holed spaces are
  adjusted through their individual wall segments.
- Select a wall to show both endpoint circles and a center square immediately,
  in 2D and 3D. Drag an endpoint to move only that end, keeping the other fixed;
  free XY movement supports angled walls. Drag the center square to translate
  the whole wall and its hosted openings. No inspector mode switch is needed.
  Only the center square starts a segment drag, so its hit target cannot cover
  the endpoints. Exact X/Y offsets remain available in the inspector. Other
  walls stay fixed and enclosed room boundaries/areas update. Railings expose
  the same three handles.
- Meeting wall faces join at their offset-line intersections, filling the
  outer corner without moving either centerline. Isolated ends keep flat caps;
  visible gaps are not silently bridged. The plan, 3D model and measured wall
  footprint share these joins. An inner branch at an exterior corner does
  not disable its mitre; intentional wall-thickness steps are retained.
- Select a wall to edit its height and thickness. Translation preserves the
  sizes of its openings. Endpoint edits retain each opening's physical distance
  from the stationary endpoint and rotate it with its host. A collapsed wall
  or one too short to contain its openings rejects the edit atomically.
- Select a door/window to reveal its two ends and center in the plan, plus
  four edges and a center in 3D and the inspector's elevation editor. The
  center moves the whole rectangle without resizing it; a left/right edge
  changes width while keeping the opposite edge fixed; a top/bottom edge
  changes height while keeping its opposite fixed. In 2D and 3D, drag the
  center in the floor plane to transfer the opening onto another wall. The
  preview turns with that wall, and release updates the host, room ownership
  and wall cut atomically. Drop within 600 mm of a valid placement; the full
  opening must fit with 25 mm end margins and clear other openings. Windows
  and entrance doors stay on exterior walls. Sizes and base height are retained.
  Doors also offer **Flip swing direction** and **Swap hinge side**; both
  affect 2D and 3D and persist in saved JSON. Rotation onto a different wall
  follows the host angle; the cut remains attached to a wall.
  The inspector's elevation center still moves along its current host and
  vertically. Vertical movement changes the sill/base height; no opening
  can extend below the floor or above its wall. Doors initially start at zero.
  The same values remain available as numeric width, height, position and
  sill/base inputs.
- Dragging displays an outline preview and commits one atomic edit on release.
  Node snapping is enabled by default in both 2D and 3D. Endpoints and
  intersections have priority within 12 screen pixels; nearby wall-line
  projections support T junctions within 8 pixels. Whole-segment snapping
  preserves its shape. Toggle **Snap** or press S; hold Alt to bypass both node
  and grid snapping. Other placements use the 100 mm grid. Arrow
  keys move the focused control by 100 mm.
  In opening elevation/3D controls, left/right follows the wall and up/down
  changes elevation. Rotate or zoom the 3D view for a clear facade, or use the
  elevation editor when the opening is edge-on in 3D.
- Select a railing to change its height. Balcony exterior edges remain open.
- Drag blank space with the left mouse button to pan the plan. Select **Pan**
  (H) to drag anywhere, including over rooms, or hold Space while dragging.
  **Select** (V) restores element/corner editing. Right/middle dragging also
  pans. Scroll or use +/− to zoom; **Fit** restores the complete plan.
- Switch between **2D plan**, **Split view**, and **3D model** above the canvas.
  Drag the 3D view to orbit and scroll to zoom. **Top** shows the plan from
  above; **Reset view** restores the perspective. **Save PNG** exports the
  current perspective as a 2048 × 1536 image. Click an element for properties.
- Undo/redo covers accepted model changes. Ctrl+Z and Ctrl+Shift+Z also work
  when focus is outside an input field.
- **Save model** downloads the current editable document. **Open JSON**
  reopens a Text2Floorplan schema 1.0 document (including earlier Text2Revit exports). Browser refresh clears unsaved
  edits, so save before closing or refreshing the page.

Free wall edits preserve the edited wall geometry when saving, importing or
changing properties; walls are not regenerated from room polygons. After an
edit, the editor identifies closed regions from current walls and balcony
railings, subtracts wall footprints and recalculates room and total net areas.
The 2D fills, labels and 3D floors follow these regions, including angled walls
and holes. Balcony floor area is included.

A broken boundary shows **Not enclosed**, without retaining a misleading old
room area; the total is explicitly labelled partial and excludes that room.
Snapping the wall nodes back together restores its area. Merged rooms share one
region counted once in the total; split and unassigned regions are reported
separately rather than inventing individual room areas. Explicit room-handle
edits are available for uniquely matched closed rooms without holes.

Existing generation minima produce warnings during manual editing instead of
replacing the user's model. Invalid room polygons and unhosted/oversized openings reject an edit. Openings on the same
wall keep their spacing checks. Cross-wall opening-spacing conflicts become
warnings after free wall editing. Moving an opening directly still rejects
cross-wall spacing conflicts. Generation heuristics do not prevent
independent wall placement. Inference retains its original strict checks.

**Generate layout** uses the production `backend_cli.py` in a separate local
Python process. Progress appears in the status bar; **Cancel** terminates that
inference process. One job runs at a time. Requests, logs and generated plans
are written to ignored `outputs/web_editor/<job-id>/` folders.

## Current scope

This is a single-user local browser workstation. It binds only to `127.0.0.1` and
is not intended for public hosting. Frontend assets are local, without a CDN,
Node.js build, or browser-side PyTorch dependency. Inference stays on the local
Python backend and uses its existing GPU/CPU behavior.

The 3D view constructs wall solids around actual door/window openings, frames,
door leaves, floors and railings. Those objects are generated from the same
editable document as the plan, rather than a rendered image or screenshots.
This version supports closed-room boundary edits, independent angled wall
segments, node snapping and wall-derived floor areas. It does
not yet add/delete rooms, create arbitrary new walls, support multiple floors,
or provide Revit family editing, IFC/GLB export, or collaboration.

Saved JSON retains the existing Revit input schema. This version does not
write `.rvt` files or automatically import edited files through a new Revit
command. Native Revit output still requires the Revit add-in; an explicit
edited-JSON import command is a separate next step.

## Code and checks

- `model_document.py`: atomic import/edit, shared geometry and hosted openings.
- `enclosed_areas.py`: closed-space reconstruction, net areas and floor meshes.
- `wall_editing.py`: separate wall translation and endpoint edits with host retention.
- `opening_editing.py`: atomic opening transfers, orientation, dimensions and door flips.
- `server.py`: local HTTP entry, editing requests and inference lifecycle.
- `static/app.js`: SVG plan, selection, property editing and document history.
- `static/plan_navigation.js`: independent plan pan/zoom and tool shortcuts.
- `static/edit_handles.js`: shared plan, elevation and 3D edit controls.
- `static/node_snap.js`: screen-distance node/intersection and T-junction snapping.
- `static/opening_placement.js`: wall projection and cross-wall opening previews.
- `static/scene.js`: local WebGL geometry, orbit camera and 3D picking.

```powershell
python tests/test_web_editor.py
python tests/test_edit_handles.py
python tests/test_wall_independence.py
python tests/test_enclosed_areas.py
python tests/test_opening_placement.py
node --test tests/test_plan_navigation.mjs
node --test tests/test_edit_handles.mjs
node --test tests/test_node_snap.mjs
node --test tests/test_opening_placement.mjs
```

The browser front end can later be embedded in a desktop wrapper while keeping
the same editable-document interface and inference backend.
