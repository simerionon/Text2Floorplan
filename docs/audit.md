# Publication audit

Audit date: 2026-10-02. The publication directory is `final`; the parent workspace
contains local assets and preserved historical work and is not the upload root.
Public release download verification: 2026-10-03.
ResPlan source pipeline consolidation: 2026-10-03.
RPLAN and feature pipeline consolidation: 2026-10-03.
Local browser editor verification: 2026-10-19.
Windows release refresh and MIT licensing: 2026-10-23.

## Inference entry and documentation review — 2026-10-26

- The complete production inference code was already tracked in the source
  repository: `pipeline_generate.py`, `backend_cli.py`, `inference_runtime.py`,
  `flow_solver.py` and their model/geometry dependencies. The separate `raster/`
  FM/DDPM research track and historical archived pipelines were inspected and
  were not copied into the production repository.
- Added `infer.py`, a direct prompt-to-PNG/editable-JSON entry using the existing
  production backend. It supports full/compact PTHs, explicit CLIP paths,
  automatic GPU/CPU selection and forced CPU. Request files are temporary;
  generated output remains ignored by Git. English and Chinese inference guides
  describe the same backend used by the browser workstation and Revit plug-in.
- Compared the actual release checkpoint with the supplied training PTH. All
  345 production `model` tensors and their dtypes match exactly, as do retained
  architecture arguments. The training file is 770,009,261 bytes; its export is
  193,053,154 bytes. Removal of the EMA copy and optimizer/training state explains
  the difference; no model quantization or pruning was performed.
- Reviewed every current public README: root, browser workstation, sample, data,
  models and checkpoints, in both languages. Updated the release notes,
  portable/Revit guides, development notes and workspace index. The independent
  launchers, local inference without LLM/API keys, source versus bundled setup,
  browser editing and native Revit scope are now explicit. The two pairs of
  browser/Revit example images remain in both root README files. Historical
  archive documentation retains its original context.
- Corrected the older blanket statement assigning the source-code license to
  weights without reviewing training-data permissions. Source-code licensing
  and dataset/weight distribution permissions are documented separately.
- Four new CLI entry checks passed. Real generation with the compact release PTH
  produced a PNG and application-schema JSON from a working directory outside
  the source repository, using the same production backend and local CLIP model.
  Generation also passed with the original full PTH on CPU and a minimal Windows
  PATH. The resulting JSON imports into the browser workstation. All 112 Python
  regression checks passed after the changes.

## Windows release refresh — 2026-10-23

- Repository/browser branding is Text2Floorplan; the native integration is
  Text2Floorplan Revit. Public README files retain both pairs of browser and
  native Revit illustrations, with each sample's own scale and provenance.
- Original project material now uses the standard MIT License, copyright 2026
  Simon H.; no evaluation-only restriction remains in the current license.
- The Windows browser release bundles Python, PyTorch, CLIP and inference-only
  Flow weights. It supplies a complete offline ZIP and a main ZIP plus four
  independent data ZIPs. Data hashes and paths are checked before extraction.
- A freshly extracted runtime passed dependency checks and real GPU and CPU
  generation. The real CMD entry prepared the environment and opened localhost.
  Browser editing, legacy Revit JSON import and inference use the same backend.
- All Revit 2020–2026 targets were rebuilt with the new display name. The setup
  and uninstaller use separate build outputs, preventing either from cleaning
  the other's executable. Setup error logging no longer masks the original
  exception when a log file cannot be written.
- Ten installer extraction/download checks passed. The renamed uninstaller was
  run twice in an isolated test root; generated jobs, family data, preferences
  and unrelated registrations were retained.
- The new online setup targets the `v1.1.0` release under
  `Simon777hh/text2floorplan`. Source/payload hashes, version-specific DLLs,
  models and numbered download data were checked. Native model construction
  was historically verified in Revit 2022; the renamed build has not been
  re-run inside every Revit version. A clean external-PC trial and the new
  public download URLs remain pending publication.

## Fixed

* Mixed T junctions now retain the corner join between their two exterior
  walls. Previously, every three-way node skipped corner construction. Corner
  additions are clipped against existing wall bodies; wall centerlines and
  opening positions remain unchanged. Normal thickness steps remain intentional.
  The actual edited model and minimized mixed/straight T regressions passed.
* Removed confirmed editor debug screenshots, replay exports, scene dumps,
  one-off patch helpers and Python caches after verification. Unique user model
  snapshots are preserved outside the publication directory.

* Updated the public sample to the current large calibration (0.0546657873 m per
  canvas unit), including opening widths, room/total areas, JSON, metadata and
  matching 2D/WebGL images. Root documentation now identifies these as editor
  illustrations rather than claiming new native Revit verification.
* Reproduced an omitted outer quarter-square where two wall rectangles stopped
  at their shared centerline endpoint. Offset wall faces now meet at a bounded
  mitre intersection. Joined footprints drive both area routines and 2D/3D
  corner solids, while centerline edits remain independent. Ten regression
  checks cover moved/rejoined corners, mixed/straight T nodes, calibration, right angles, unequal thicknesses, gaps, T joins,
  independent moves and inner-enclosure corner slivers. Corrected inward box
  normals so wall and corner lighting agree; browser PNG export uses the actual
  WebGL renderer at 2048 × 1536 pixels.

* Added a Revit-independent local browser editor with linked SVG plan and WebGL
  model views. Atomic document edits propagate shared corner constraints and
  retain hosted openings, dimensions, clear areas and open balcony railings.
  Existing inference runs in a cancellable local process. The English-first UI
  includes Chinese, undo/redo and JSON import/export. The browser product is
  named Text2Floorplan, with English `/en` and Chinese `/zh` entry pages. See
  [the editor guide](../web_editor/README.md) for prototype scope and setup.
* Fixed 2D navigation, which previously accepted only right-button dragging.
  A replay of the production handlers failed for left dragging and passed for
  right dragging before repair. Background left dragging, explicit Pan and
  Space dragging now share a viewport-only navigation module. Nine regression
  checks cover selection isolation, transformed coordinates, pointer capture,
  click suppression and anchored zoom. Edge browser checks confirmed left
  dragging and Pan change the SVG viewBox without changing its scale.
  The redesigned English/Chinese interface includes larger work areas, three
  view modes, a floating plan toolbar, room list and clearer property inputs.
* Added direct edit handles shared by plan, perspective and opening elevation
  views. Walls/railings expose two endpoints and a center; rooms expose corners,
  edges and a center; opening rectangles expose four edges and a center in
  elevation/3D. Center edits preserve dimensions and edge edits keep the opposite
  edge fixed. Room-boundary movement propagates orthogonal constraints; independent
  wall behavior is described below. Opening base height is editable for doors as well as windows;
  floor, host-wall, spacing and dimension checks still reject invalid edits.
  Browser drags verified 3D wall translation, window top-edge resizing and whole
  window translation; 3D handle keyboard edits updated window width. Downloaded
  JSON confirmed 1293.435 mm width, 1300 mm height and 1100 mm sill height. The
  user's existing edited 133.1 m² document was exported and retained separately.
* Decoupled wall translation from endpoint editing. The minimized replay showed
  endpoint XY displacement being clamped and segment moves changing room/neighbor
  geometry. Separate `translate_wall` and `move_wall_endpoint` commands now edit
  authoritative wall segments without shared-corner propagation. Selecting a wall now
  shows both endpoints and its center together in 2D/3D, with no mode switch.
  The center target no longer spans the full wall and cannot intercept endpoint
  drags. XY offsets and Alt fine placement remain available.
  Endpoint rotation keeps the opposite end fixed and retains hosted openings.
  Import and parameter changes preserve independent walls; explicit closed-room
  handle edits transform the selected physical boundary group.
  All 28 sample walls pass individual translation checks with neighbors fixed;
  browser mouse drags confirmed that the endpoint circle changes only one end,
  while the center square translates both ends equally with neighbors fixed.
  Both views expose all three handles simultaneously; no mode switch remains. Wall-derived enclosures now replace the earlier reference-only area labels.
  Closed cells from walls and balcony railings are measured after subtracting
  wall footprints; 2D fills, labels and triangulated 3D floors share the result.
  Open rooms have no numeric area, merged cells count once, and split/unknown
  cells are reported. A browser drag restored the original wall coordinates
  exactly and recovered 106.234745 m² from the partial 65.6 m² state; exported
  JSON reimport and floor-triangle area sums matched. Undo/redo and the snap
  toggle/shortcut were checked. Node snapping prioritizes endpoints/intersections and
  supports wall-line T junctions in 2D/3D; S toggles it and Alt bypasses it. Cross-wall opening clearances
  warn instead of blocking manual wall placement; host-fit checks remain strict.

* The editor now starts empty. Three clickable English prompt examples cover
  small, default medium (size omitted) and large apartments. English/Chinese
  empty states, parameter template, import-sample action and responsive prompt
  cards were verified in the browser.

* ResPlan preparation now has one raw-to-filtered-canvas entry point. Separate
  clean/rebuild/filter dataset versions and the extra canvas CLI were removed.
  Corner extraction and wall reconstruction are retained as internal modules.
  GT, prompt preparation and RPLAN scaling use the same final ResPlan file;
  recorded transforms recover source units in memory for source-scale rules.
* `data/` now documents all six retained statistical/configuration files and
  distinguishes them from locally generated training datasets and model weights.
* RPLAN conversion, filtering and CLIP area calibration now use one entry and
  one prepared file. Its source geometry stays unchanged, and a recorded area
  multiplier replaces separate CLIP scaling files. Topology now applies the
  bedroom edge policy before saving. Attention masks and next-corner mapping
  are generated in one GT pass. Six redundant public stage scripts were removed.
  Two unused mask builders were removed from raw extraction; training attention
  builders now reside in `prepare_attention.py`.

* All room windows exclude the entrance's continuous exterior facade, including
  collinear split segments. Separate parallel facades remain eligible. Bedrooms
  connected to balconies keep their access door and receive no extra window.
* Door placement now searches clear alternative positions. Openings keep at
  least 200 mm between reference segments. Perpendicular doors sharing a room
  keep 350 mm; opposed parallel doors with overlapping projections require the
  larger door width plus 100 mm. These checks span different host walls, rather
  than checking only overlap on one wall. Unplaceable required doors reject the
  layout instead of being silently omitted.
* A physical cleanup step removes narrow room appendages below 600 mm by
  transferring small patches to a neighboring room. Small narrow gaps can be
  filled. A whole narrow room, disconnected body, excessive repair or residual
  narrow appendage rejects the layout. Occupied floor area is preserved. The
  reported sample's 370 mm bedroom strip was removed before door placement.
* Only kitchen and bathroom have area thresholds, each 2 m². Preview estimates
  subtract wall footprints. Revit plans label each native room area and their
  sum, including balconies. Invalid geometry, missing doors and small areas
  retry up to ten attempts, including requests with an initial explicit seed.
* Window solid height/sill validation and the corrected cached window family
  origin are retained. Balcony outside edges use railings and separation lines.
* RPLAN filtering matches polygons by room name rather than assuming topology
  indices survive removal of the front-door placeholder.
* CLIP now stores explicit aligned plan IDs. Current pooled vectors were
  regenerated from 269 unique prompts and expanded to 75,379 ordered rows.
* Compressed GT caching and mask validation stream large arrays to avoid the
  validator's previous memory allocation failure. Training requires CLIP IDs.
* Personal model paths, obsolete file references, decorative comments and unused
  demo entry points were removed. Thirty-five unreachable postprocessing
  definitions (1,843 lines) were removed after checking the production call
  graph. Historical source remains archived locally.
* The installer manifest was restored and the installer successfully rebuilt.
  The release now includes the current backend, physical policies and notices.
* Runtime and inference models are compressed from their original files using
  LZMA2. The Windows online installer retrieves two release data attachments,
  resumes partial downloads and checks their individual and combined hashes.
  It validates all extracted files before initializing Python. Long-path file
  access was corrected after a full trial exposed a deeply nested runtime path.

Opening placement was also checked in Edge using the bundled sample: Door 2
moved from horizontal `wall_002` to vertical `wall_013` without changing its
width, height or base elevation. The old wall cut was restored, the new cut
followed the host, and swing/hinge flips updated the plan and linked 3D model.
The English and Chinese inspector controls were checked. This validation is
for the browser editor; native Revit hinge handling was not tested here.

## Verification

| Check | Result |
| --- | --- |
| Local editor document contracts | Full current Python suite: 108 tests passed, including opening placement and Windows ZIP packaging contracts |
| Independent wall segments | 11 regression tests include every sample wall; browser export/import retained the slanted wall with all other wall segments fixed; derived room boundaries follow current enclosures |
| Browser edit handles and navigation | 31 JavaScript checks passed; host placement previews, hinge/swing geometry, navigation and wall handles checked |
| Editor HTTP interface | Import/edit/reopen, invalid-edit rejection, origin guard, traversal guard and JS content type passed |
| Editor browser trial | Real NVIDIA GPU inference loaded a six-room plan; wall height, shared-corner edits, window parameters, undo/redo, cancellation, language switching and JSON download checked |
| Geometry/opening/area regressions | 22 tests passed |
| Prepared GT, topology, masks, mapping, CLIP | All 75,379 rows verified |
| ResPlan raw → filtered canvas | Two real source plans match the prior four-stage output; GT, topology, masks and IDs also match |
| ResPlan canvas/data contract | Eight regression checks passed |
| RPLAN and feature consolidation | 30 prepared source plans retained the same 23 IDs; GT, topology, masks, mapping and prompts matched the former stages exactly |
| Consolidated preprocessing contracts | Eight additional tests passed; 38 unit tests passed in total |
| Raw RPLAN PNG entry | Two conversions matched the former converter; parallel execution, rejection reports and CLI guards passed. Both samples were rejected by the retained filter |
| Real packaged-runtime GPU inference | Passed with the corrected sample seed |
| Native Revit 2022 construction and exports | Nine rooms, real doors/windows, open railings and room/total area notes |
| Entrance facade / balcony bedroom / spacing checks | Accepted JSON passed |
| Revit API targets | 2020–2026 DLLs compiled |
| Release payload and source | Payload hash, 32,696 runtime/model files, current backend and seven DLLs verified |
| Installer extraction and download regressions | 10 checks passed, including long paths, traversal, integrity, resume and cache reuse |
| Full online installation using local download fixtures | Production setup code and data installed successfully; Python/PyTorch/model health check and seven isolated add-in registrations passed |
| Runtime CPU / NVIDIA checks | CPU and GPU health checks passed using the same packaged runtime/model files |
| Release attachments | Setup EXE and both data parts verified against SHA256.txt; all four assets below 2 GiB |
| Published GitHub v1.0.0 | All four server-reported hashes and sizes match local assets; setup/checksum HTTPS downloads and both data parts' byte-range responses verified |
| Git publication | Source repository excludes weights and installers; inference weights supplied by release data |

`sample/floorplan.png`, `sample/model3d.png`, `sample/plan.json` and
`sample/model-metadata.json` describe one matching recalibrated layout (128.9 m²). The updated
images use local editor geometry; native Revit measurements for this scale
have not been rerun. Detailed
logs and generated RVT/build products are local assets, excluded from Git.

The historical October 2 Windows online installer was version `1.0.0-20261002233122`,
3,573,261 bytes (3.41 MiB). Its data attachments are 1,610,612,736 and
1,001,222,741 bytes (1.50 and 0.93 GiB). The earlier complete ZIP installer was
3.63 GiB; a complete LZMA2 comparison build was 2.44 GiB. Neither complete
installer fits GitHub's 2 GiB per-asset limit. The online release uses tag
`v1.0.0`; its attachment names and configured download URLs must agree.
macOS and Linux installers are outside the first release's scope.

The former native sample total was 106.2 m², with 28 wall segments; its
original images/JSON are now also retained as the public `sample/revit-*` pair.
The browser sample uses the current
large scale and measures 128.888219 m² net, with the same layout and seed. Prepared
training data, downloaded CLIP and build caches were physically moved to the
parent workspace's `_local_assets/` directory. The active sample RVT and loaded
DLLs remain in ignored local output directories so this Revit session remains
usable.

## Repository cleanup

The public feature pipeline contains only current raw/normalized GT, topology,
prompt, mask, edge mapping, pooled CLIP and their validator. Optional priors,
alternate loss-target generators, exploratory analysis and old visualizers were
moved out. Unique historical experiments, dataset backups and earlier source
were archived instead of deleted. Raw/prepared datasets, downloaded CLIP,
SDK/runtime caches, build outputs and installer binaries are local assets.

Only confirmed derived junk is deleted: Python bytecode caches, an accidental
file containing an `rg` error, and the redundant payload ZIP after its complete
bytes were verified inside the installer. Active installed runtime files remain
at their original location so the Revit registration continues to work. No
parent Git history, original supplied checkpoint or unique dataset was deleted.

## Remaining limits

* Native runtime verification covers Revit 2022. Other Revit versions compiled,
  but still need actual runtime testing. A clean external-PC install remains
  unverified. Binaries are unsigned.
* The online install trial used a loopback HTTP fixture in isolated test mode,
  with the production executable code and full data attachments unchanged.
  Normal installation requires HTTPS. The public setup and checksum downloads,
  HTTPS redirects and both data parts' range responses were checked after
  publication. A complete installation downloading all data from GitHub still
  requires an end-to-end user trial; the remote data parts were sampled rather
  than downloaded again in full.
* NuGet's online vulnerability feed was unavailable during compilation
  (`NU1900` warnings). Successful builds do not establish a clean dependency
  vulnerability audit.
* Exact raw-to-historical-dataset reproduction is not established; the earlier
  complete batch driver was unavailable. The current retained reconstruction
  core was checked on two real samples and current training tensors were fully
  verified. See [data_pipeline.md](data_pipeline.md).
* Minimum areas and conservative spacing checks improve output quality but do
  not establish architectural or accessibility code compliance. Door-spacing
  guards do not simulate every native hinge/swing configuration.
* Original project material is now under MIT, copyright 2026 Simon H. This
  replaces the previous evaluation-only license for this release and permits
  commercial reuse with the MIT notice retained. Third-party and dataset terms
  remain separate. A complete dependency-provenance review was not performed.

The local Revit registration points to the updated area-label assembly for its
next startup. The current session's old ribbon assembly stays loaded until
Revit restarts; sample validation used the freshly compiled production builders.
