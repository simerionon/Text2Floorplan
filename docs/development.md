# Development and release packaging

## Shared inference and independent interfaces

`infer.py`, the browser workstation and the Revit add-in use the same production
`backend_cli.py`. Source CLI usage, model paths and PNG/JSON outputs are documented
in [English](inference.md) and [Chinese](inference.zh.md). This path does not import
the trainer or require generated training tensors, an LLM or an external API.

The Windows browser workstation and Revit plug-in have independent launchers and
runtime/model copies. Users select one edition; installing the other is optional.
The browser preserves editable JSON and renders 2D/3D geometry. Native Revit
families and RVT project content are created only through the Revit API.

## Windows browser edition

Use a prepared Windows x64 Conda environment with `requirements.txt` installed.
Pack it with `conda-pack==0.8.1` into a ZIP containing `python.exe` and
`Scripts/conda-unpack-script.py`. Supply an inference-only models directory
containing `flow_matching_best.pth` and the complete `clip/` text encoder.

```powershell
python -m pip install conda-pack==0.8.1
conda pack -p C:/Envs/Text2Floorplan -o web_editor/build/runtime.zip --format zip
python -m web_editor.build_release --runtime-zip web_editor/build/runtime.zip --models C:/Models --output web_editor/dist
```

Create `web_editor/build` before packing. The builder uses explicit application
file lists and excludes datasets, training state, IDE settings and Git metadata.
It creates a small `Text2Floorplan-Web-Windows.zip`, numbered independent data ZIPs,
a complete offline ZIP and `SHA256-web.txt`. Each data ZIP is below 2 GiB. Upload the
main ZIP, **all** data ZIPs, checksums and release notes together. The complete
offline ZIP exceeds that per-file limit; distribute it through another host.
The portable launcher validates data hashes and paths, extracts locally, runs
Conda relocation and checks inference dependencies before opening localhost.
It does not register a service or a Revit add-in. Generated output stays in the
extracted directory and is excluded from source control.

The repository and browser product are Text2Floorplan. The optional Revit
product is **Text2Floorplan Revit**, with `text2floorplan_revit-Setup.exe` and
`text2floorplan_revit-Uninstall.exe`. Existing `Text2Revit` assembly namespaces,
registration GUID, local data directory and registry key are retained for
compatibility with earlier installations. User-facing ribbon and dialog names
use Text2Floorplan.

## C# files

`revit/Text2Revit.Addin/App.cs` registers the ribbon button. `Command.cs` opens
the prompt dialog and creates the model in one undo group. `UI/PromptDialog.cs`
handles language, examples, inference progress and cancellation.

`Services/PythonBackendRunner.cs` launches the bundled backend and consumes its
JSON. `JsonPlanReader.cs` validates the schema. `WallBuilder`, `BalconyBuilder`,
`FamilyLibrary`, `OpeningBuilder`, `RoomBuilder` and `ModelViewBuilder` create
native 3D elements, hosted door/window families, area notes and the model view.
`OpeningGeometryValidator` checks the actual window solid against sill/height
dimensions, including family insertion-origin offsets.

The installer copies the runtime/models/add-ins into the current user's local
application data, writes version-specific `.addin` registrations and adds an
uninstaller. End users do not place C# source or DLLs manually.

The release also includes `text2floorplan_revit-Uninstall.exe`, a standalone uninstall
tool that opens directly in uninstall mode without an installation payload or
command-line arguments. Close Revit, run it under the Windows account that
installed Text2Revit, and click Uninstall. It removes product releases, owned
Revit registrations, download caches and the Windows uninstall registration;
generated jobs, family caches and preferences are preserved.

## Build

From the repository root:

```powershell
python -m pip install -r requirements.txt
python scripts/setup_models.py
python revit/build_release.py --checkpoint checkpoints/flow_matching_best.pth
```

Or use `revit/Build-Release.cmd`. `TEXT2REVIT_BUILD_PYTHON` selects the prepared
Python environment to bundle. Packaging needs a Windows Conda environment and
Conda tooling; Conda is only a developer dependency. First builds download the
.NET SDK, API reference packages and packing tools into ignored `revit/build_tools`.
`REVIT2022_API_DIR` (and equivalent years) selects locally installed API files.

Build only the small standalone uninstall tool, without packaging models or
the Python runtime:

```powershell
python revit/build_release.py --uninstaller-only
```

This writes `revit/dist/text2floorplan_revit-Uninstall.exe` and updates its entry in
`SHA256-revit.txt`. Full release builds include this tool too.

The builder compiles Revit 2020–2026 plugins, exports the production model and
architecture arguments without EMA/optimizer/training state, copies the CLIP text encoder, packs Python/PyTorch,
assembles `revit/dist/text2floorplan_revit-Setup.exe` and verifies its appended payload hash.
Runtime/build caches are reusable. It also writes `SHA256-revit.txt`.

By default, the original runtime and model files are compressed together into
a solid LZMA2 archive with a 128 MiB dictionary. The installer bundles the
public-domain LZMA SDK extractor, validates archive paths against a file
inventory and checks each extracted file's size and SHA-256 before initializing
Python. No user-installed archive tool is required. The intermediate runtime
ZIP is a build cache and is expanded before LZMA2 compression. Use
`--compression zip` for the previous ZIP-based payload format.

### GitHub online installer

Build the small online installer and data attachments for a specific tag:

```powershell
python revit/build_release.py --checkpoint checkpoints/flow_matching_best.pth --online-release-url https://github.com/Simon777hh/text2floorplan/releases/download/v1.1.0
```

Upload `text2floorplan_revit-Setup.exe`, all `environment.7z.*` parts and `SHA256-revit.txt` from
`revit/dist/` to that release. Keep asset names and the configured tag unchanged:
their URLs are embedded in the installer. Each data part is at most 1.5 GiB.
Publish all assets together so the installer can retrieve its complete payload.
Also upload `text2floorplan_revit-Uninstall.exe` to offer standalone removal.

The installer uses HTTPS and the Windows system proxy, reuses validated cached
parts, requests byte ranges for interrupted downloads and checks per-part and
combined SHA-256 values. Successful installation removes its download cache.
Inference works offline after installation. Isolated `--test-root` checks also
permit loopback HTTP for local fixtures; normal installation requires HTTPS.
During installation, Cancel or the window close button requests cancellation.
Setup interrupts downloads, stops the active extractor or Python process, and
removes the incomplete release before allowing the window to close. Download
cache files remain available for a later retry. File copying and verification
also check cancellation. Final add-in and uninstaller registration is a short
commit step after the cancellable checks; once committed, setup completes.
Uninstallation must finish once started.
The extractor and .NET file operations support long installation paths. The
installer regression script covers extraction, traversal rejection, integrity,
long paths, resumed downloads and cache reuse.

The first release targets Windows x64 only. No macOS or Linux installer is
included.

| Revit | Target framework |
| --- | --- |
| 2020 | .NET Framework 4.7 |
| 2021–2024 | .NET Framework 4.8 |
| 2025–2026 | .NET 8 Windows |

All seven targets were compiled locally. Native model construction was tested
in Revit 2022 only. A clean external-PC installation and other Revit runtime
versions remain release validation tasks. The current binaries are unsigned.

## Distribution

The source repository excludes model weights, generated datasets, downloaded
CLIP files, build caches and installer outputs through `.gitignore`. Source
inference and release builds require a separately supplied compatible checkpoint.

The full training checkpoint is kept locally. The builder removes the EMA copy,
optimizer and other training state and bundles only the production `model` and
architecture arguments with the CLIP encoder. The original 770,009,261-byte PTH
and the 193,053,154-byte export have identical production model tensors; no
quantization or pruning is applied. Both formats work with source inference,
but only the full checkpoint retains the optimizer/EMA state used to resume training. Complete Windows
editions supply the compact PTH automatically. Git LFS is not required for the
source repository. Weight and dataset permissions must be reviewed separately
from the source-code license; see [checkpoint details](../checkpoints/README.md).

The complete LZMA2 offline installer is approximately 2.44 GiB, compared with
3.63 GiB for the earlier ZIP build. The online setup executable is approximately
3.4 MiB and downloads two data attachments of 1.50 GiB and 0.93 GiB. These can
be hosted together in a GitHub release. Distribute the complete offline installer
through a download service that accepts its size. Confirm the host's current
per-file limits before publishing. See
[GitHub's release documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).

## Checks

```powershell
python -m unittest discover -s tests -v
python -m preprocessing.features.validate_final_training_data
python tests/verify_opening_placement.py outputs/verification/plan.json
python tests/verify_installer_compression.py --stub revit/Installer/bin/Release/net47/Text2Revit.Setup.exe --extractor revit/build_tools/lzma/sdk/bin/x64/7zr.exe --work-dir outputs/installer-compression-tests
python tests/verify_installer_cancellation.py --stub revit/Installer/bin/Release/net47/Text2Revit.Setup.exe --work-dir outputs/installer-cancellation-tests
python tests/verify_uninstaller.py --tool revit/dist/text2floorplan_revit-Uninstall.exe --work-dir outputs/uninstaller-tests
revit/dist/text2floorplan_revit-Setup.exe --verify-only
```

`tests/verify_opening_placement.py` independently checks a real generated JSON:
all windows avoid the continuous entrance facade, and bedrooms connected to
balconies have no window. Unit tests cover collinear split walls, different
parallel walls, balcony access, minimum areas and wall-footprint subtraction.
No automated test is claimed to establish architectural code compliance.

The Windows cancellation probe drives the actual setup form with a stalled
loopback download and an isolated installation root. It checks both Cancel and
window close, release rollback, preserved download cache, and termination of
extractor/Python child processes. Use a fresh work directory for each run.
