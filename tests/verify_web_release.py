"""Verify the distributable browser package, inventory, source and data hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from web_editor.build_release import application_files, digest, safe_name


def verify(folder, deep=False):
    with zipfile.ZipFile(folder / "Text2Floorplan-Web-Windows.zip") as package:
        manifest = json.loads(package.read("Text2Floorplan/web_editor/release.json"))
        assert manifest["product"] == "Text2Floorplan" and manifest["license"] == "MIT"
        for name, source in application_files().items():
            assert package.read("Text2Floorplan/" + name) == source.read_bytes(), name
        assert package.read("Text2Floorplan/LICENSE").decode("utf-8").splitlines()[0] == "MIT License"
    expected = {f["path"]: f for f in manifest["files"]}
    assert len(expected) == len(manifest["files"])
    assert {"runtime/python.exe", "runtime/Scripts/conda-unpack-script.py", "models/flow_matching_best.pth",
            "models/clip/model.safetensors"} <= set(expected)
    seen = set()
    for part in manifest["parts"]:
        source = folder / part["name"]
        assert 0 < source.stat().st_size == part["size"] < 2**31
        assert digest(source) == part["sha256"], source.name
        with zipfile.ZipFile(source) as package:
            for entry in package.infolist():
                safe_name(entry.filename)
                assert entry.filename.startswith(("runtime/", "models/"))
                assert entry.filename not in seen
                seen.add(entry.filename)
                assert expected[entry.filename]["size"] == entry.file_size
                if deep:
                    with package.open(entry) as stream:
                        assert hashlib.file_digest(stream, "sha256").hexdigest() == expected[entry.filename]["sha256"]
    assert seen == set(expected)
    for line in (folder / "SHA256-web.txt").read_text().splitlines():
        checksum, name = line.split("  ", 1)
        assert digest(folder / name) == checksum, name
    offline = folder / "Text2Floorplan-Web-Windows-Offline.zip"
    if offline.is_file():
        with zipfile.ZipFile(offline) as package:
            for part in manifest["parts"]:
                with package.open("Text2Floorplan/" + part["name"]) as stream:
                    assert hashlib.file_digest(stream, "sha256").hexdigest() == part["sha256"]
    return {"ok": True, "version": manifest["version"], "data_parts": len(manifest["parts"]),
            "runtime_model_files": len(expected), "source_matches": True, "deep": deep}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.folder, args.deep), indent=2))
