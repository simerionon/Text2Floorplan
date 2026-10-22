"""Packaging contracts for independent, checksummed Windows data ZIPs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from contextlib import redirect_stdout
from io import StringIO
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_editor import build_release as builder


class WebReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = self.root / "runtime.zip"
        with zipfile.ZipFile(self.runtime, "w") as z:
            z.writestr("python.exe", b"MZ" + b"a" * 700)
            z.writestr("Scripts/conda-unpack-script.py", "print('relocate')")
            z.writestr("Library/bin/library.dll", b"MZ" + b"b" * 700)
        self.models = self.root / "models"
        (self.models / "clip").mkdir(parents=True)
        (self.models / "flow_matching_best.pth").write_bytes(b"checkpoint")
        (self.models / "clip/model.safetensors").write_bytes(b"model")
        (self.models / "clip/config.json").write_text("{}")
        self.output = self.root / "release"

    def build(self):
        with redirect_stdout(StringIO()):
            return builder.build(self.runtime, self.models, self.output, part_bytes=1000)

    def test_data_archives_are_independent_and_manifest_matches_every_file(self):
        launcher = self.build()
        with zipfile.ZipFile(launcher) as z:
            manifest = json.loads(z.read("Text2Floorplan/web_editor/release.json"))
            self.assertIn(b"MIT License", z.read("Text2Floorplan/LICENSE"))
            self.assertIn("Text2Floorplan/Start-Text2Floorplan.cmd", z.namelist())
            self.assertFalse(any(".git/" in n or "__pycache__" in n for n in z.namelist()))
        inventory = {r["path"]: r for r in manifest["files"]}
        seen = set()
        for part in manifest["parts"]:
            source = self.output / part["name"]
            self.assertEqual(builder.digest(source), part["sha256"])
            self.assertLess(source.stat().st_size, 2**31)
            with zipfile.ZipFile(source) as z:
                self.assertIsNone(z.testzip())
                for name in z.namelist():
                    self.assertNotIn(name, seen)
                    seen.add(name)
                    self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(), inventory[name]["sha256"])
        self.assertEqual(seen, set(inventory))
        with zipfile.ZipFile(self.output / "Text2Floorplan-Web-Windows-Offline.zip") as z:
            self.assertTrue(all("Text2Floorplan/" + p["name"] in z.namelist() for p in manifest["parts"]))

    def test_runtime_path_traversal_is_rejected(self):
        with zipfile.ZipFile(self.runtime, "a") as z:
            z.writestr("../../escape.txt", "bad")
        with self.assertRaisesRegex(ValueError, "Unsafe package path"):
            self.build()
        self.assertFalse((self.root / "escape.txt").exists())

    def test_existing_release_is_never_silently_overwritten(self):
        self.output.mkdir()
        (self.output / "existing.txt").write_text("keep")
        with self.assertRaisesRegex(ValueError, "never overwritten"):
            self.build()
        self.assertEqual((self.output / "existing.txt").read_text(), "keep")

    @unittest.skipUnless(sys.platform == "win32", "Windows launcher contract")
    def test_explorer_wrapper_finds_data_zips_in_original_download_directory(self):
        web = self.root / "downloads/Text2Floorplan-Web-Windows/Text2Floorplan/web_editor"
        web.mkdir(parents=True)
        part = self.root / "downloads/Text2Floorplan-Web-Data-1.zip"
        part.write_bytes(b"test")
        (web / "release.json").write_text(json.dumps({"version": "test", "unpacked_bytes": 0,
            "parts": [{"name": part.name, "size": 4, "sha256": "0" * 64}]}))
        script = web / "Prepare-Portable.ps1"
        script.write_bytes((builder.ROOT / "web_editor/Prepare-Portable.ps1").read_bytes())
        result = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                 "-File", str(script)], capture_output=True, timeout=30)
        # It must find the archive two levels up and reach checksum validation.
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"Checksum mismatch", result.stderr)
        self.assertNotIn(b"Missing Text2Floorplan", result.stderr)


if __name__ == "__main__":
    unittest.main()
