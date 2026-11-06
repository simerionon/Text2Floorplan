"""Build the complete offline Windows browser edition from a conda-pack ZIP.

The small launcher ZIP and numbered data ZIPs are independent release assets.
The offline ZIP includes exactly the same assets in a single download.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
BACKEND_FILES = (
    "backend_cli.py", "pipeline_generate.py", "inference_runtime.py", "revit_geometry.py",
    "plan_quality.py", "healthcheck.py", "data_generation.py", "data_utils.py",
    "topology_rules.py", "edge_utils.py", "model.py", "flow_solver.py", "runtime_utils.py",
    "plan_postprocess.py", "restore_canvas_aspect.py", "door_window_rules.py", "geometry_cleanup.py",
)
DATA_FILES = ("corner_count_distributions.json", "room_aspect_ranges.json", "room_aspect_samples.npz",
              "raw_recovery_scale_stats.json", "geometry_policy.json", "combined_area_stats_natural.json")
WEB_FILES = ("__init__.py", "server.py", "model_document.py", "enclosed_areas.py", "wall_editing.py",
             "opening_editing.py", "Prepare-Portable.ps1", "README.md", "README.zh.md",
             "PORTABLE.md", "PORTABLE.zh.md")
STATIC_FILES = ("index.html", "app.js", "scene.js", "styles.css", "edit_handles.js",
                "node_snap.js", "plan_navigation.js", "opening_placement.js")
CLI_FILES = ("infer.py", "requirements.txt", "scripts/setup_models.py",
             "docs/inference.md", "docs/inference.zh.md", "checkpoints/README.md",
             "checkpoints/README.zh.md", "checkpoints/manifest.json")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe package path: {name}")
    return name


def application_files():
    files = {name: ROOT / name for name in (*BACKEND_FILES, *CLI_FILES, "LICENSE", "THIRD_PARTY_NOTICES.md")}
    files.update({"data/" + name: ROOT / "data" / name for name in DATA_FILES})
    files.update({"web_editor/" + name: ROOT / "web_editor" / name for name in WEB_FILES})
    files.update({"web_editor/static/" + name: ROOT / "web_editor/static" / name for name in STATIC_FILES})
    files.update({"sample/" + name: ROOT / "sample" / name for name in
                  ("plan.json", "floorplan.png", "model3d.png", "README.md", "README.zh.md", "model-metadata.json",
                   "revit-floorplan.png", "revit-model3d.png", "revit-plan.json", "revit-metadata.json")})
    files["Start-Text2Floorplan.cmd"] = ROOT / "web_editor/Start-Text2Floorplan.cmd"
    files["README.md"] = ROOT / "web_editor/PORTABLE.md"
    files["README.zh.md"] = ROOT / "web_editor/PORTABLE.zh.md"
    for source in (ROOT / "third_party").rglob("*"):
        if source.is_file():
            files[source.relative_to(ROOT).as_posix()] = source
    for name, source in files.items():
        safe_name(name)
        if not source.is_file() or source.is_symlink():
            raise FileNotFoundError(source)
    return files


def build(runtime_zip, models, output, version="1.1.0", part_bytes=1500 * 1024**2, offline=True):
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use an empty output directory; existing releases are never overwritten")
    files = application_files()
    model_files = [models / "flow_matching_best.pth", *(models / "clip").rglob("*")]
    model_files = sorted(p for p in model_files if p.is_file() and p.suffix != ".pyc")
    for required in (models / "flow_matching_best.pth", models / "clip/model.safetensors", models / "clip/config.json"):
        if required not in model_files:
            raise FileNotFoundError(required)
    output.mkdir(parents=True, exist_ok=True)
    parts, inventory, archive, current_bytes = [], [], None, 0

    def close_part():
        nonlocal archive
        if archive is not None:
            path = Path(archive.filename)
            archive.close()
            if path.stat().st_size >= 2**31:
                raise ValueError("A release asset exceeds the 2 GiB limit")
            parts.append({"name": path.name, "size": path.stat().st_size, "sha256": digest(path)})
            print(f"Completed {path.name}: {path.stat().st_size / 1024**2:.1f} MiB", flush=True)
            archive = None

    def add_stream(name, size, stream):
        nonlocal archive, current_bytes
        safe_name(name)
        if size > part_bytes:
            raise ValueError(f"File exceeds the uncompressed part budget: {name}")
        if archive is not None and current_bytes + size > part_bytes:
            close_part()
        if archive is None:
            current_bytes = 0
            archive = zipfile.ZipFile(output / f"Text2Floorplan-Web-Data-{len(parts)+1}.zip", "w",
                                      zipfile.ZIP_DEFLATED, compresslevel=5, allowZip64=True)
            print("Writing " + Path(archive.filename).name, flush=True)
        checksum = hashlib.sha256()
        count = 0
        with archive.open(name, "w", force_zip64=True) as target:
            while chunk := stream.read(4 * 1024**2):
                target.write(chunk)
                checksum.update(chunk)
                count += len(chunk)
        if count != size:
            raise ValueError(f"Input changed while packing: {name}")
        inventory.append({"path": name, "size": count, "sha256": checksum.hexdigest()})
        current_bytes += count

    try:
        with zipfile.ZipFile(runtime_zip) as source:
            names = {p.filename for p in source.infolist()}
            if not {"python.exe", "Scripts/conda-unpack-script.py"} <= names:
                raise ValueError("Provide a Windows x64 conda-pack ZIP with its relocation script")
            for entry in source.infolist():
                if not entry.is_dir():
                    with source.open(entry) as stream:
                        add_stream("runtime/" + entry.filename, entry.file_size, stream)
        for source in model_files:
            with source.open("rb") as stream:
                add_stream("models/" + source.relative_to(models).as_posix(), source.stat().st_size, stream)
    finally:
        close_part()
    manifest = {"product": "Text2Floorplan", "version": version, "platform": "windows-x64",
                "license": "MIT", "parts": parts, "unpacked_bytes": sum(f["size"] for f in inventory),
                "files": inventory, "application_files": [
                    {"path": name, "size": p.stat().st_size, "sha256": digest(p)} for name, p in sorted(files.items())]}
    return assemble_application(output, manifest, files, offline)


def assemble_application(output, manifest, files=None, offline=True):
    files = files or application_files()
    manifest["application_files"] = [
        {"path": name, "size": p.stat().st_size, "sha256": digest(p)} for name, p in sorted(files.items())]
    manifest_bytes = (json.dumps(manifest, separators=(",", ":")) + "\n").encode("utf-8")
    launcher = output / "Text2Floorplan-Web-Windows.zip"
    with zipfile.ZipFile(launcher, "w", zipfile.ZIP_DEFLATED, compresslevel=5) as package:
        for name, source in sorted(files.items()):
            package.write(source, "Text2Floorplan/" + name)
        package.writestr("Text2Floorplan/web_editor/release.json", manifest_bytes)
    if offline:
        print("Assembling the complete offline ZIP", flush=True)
        with zipfile.ZipFile(output / "Text2Floorplan-Web-Windows-Offline.zip", "w", allowZip64=True) as package:
            with zipfile.ZipFile(launcher) as source:
                for entry in source.infolist():
                    package.writestr(entry.filename, source.read(entry), compress_type=zipfile.ZIP_DEFLATED, compresslevel=5)
            for part in manifest["parts"]:
                package.write(output / part["name"], "Text2Floorplan/" + part["name"], compress_type=zipfile.ZIP_STORED)
    for name in ("RELEASE_NOTES.md", "RELEASE_NOTES.zh.md"):
        shutil.copy2(ROOT / "web_editor" / name, output / name)
    assets = sorted(p for p in output.iterdir() if p.suffix == ".zip")
    (output / "SHA256-web.txt").write_text("".join(f"{digest(p)}  {p.name}\n" for p in assets), encoding="utf-8")
    print(json.dumps({"output": str(output), "data_parts": len(manifest["parts"]),
                      "unpacked_gib": manifest["unpacked_bytes"] / 1024**3,
                      "files": len(manifest["files"])}, indent=2), flush=True)
    return launcher


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-zip", type=Path)
    parser.add_argument("--models", type=Path, help="Inference-only flow checkpoint and CLIP directory")
    parser.add_argument("--output", type=Path, default=ROOT / "web_editor/dist")
    parser.add_argument("--version", default="1.1.0")
    parser.add_argument("--no-offline", action="store_true")
    parser.add_argument("--refresh-application", action="store_true", help="Refresh application/docs, retaining verified data archives")
    args = parser.parse_args()
    if args.refresh_application:
        output = args.output.resolve()
        with zipfile.ZipFile(output / "Text2Floorplan-Web-Windows.zip") as package:
            manifest = json.loads(package.read("Text2Floorplan/web_editor/release.json"))
        for part in manifest["parts"]:
            if digest(output / part["name"]) != part["sha256"]:
                raise ValueError("Existing data archive checksum differs")
        assemble_application(output, manifest, offline=not args.no_offline)
        return
    if args.runtime_zip is None or args.models is None:
        parser.error("--runtime-zip and --models are required for a new build")
    build(args.runtime_zip.resolve(), args.models.resolve(), args.output.resolve(), args.version, offline=not args.no_offline)


if __name__ == "__main__":
    main()
