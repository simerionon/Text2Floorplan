"""Public inference entry: isolated device settings, paths and failure cleanup."""
from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import infer


class InferenceEntryTests(unittest.TestCase):
    def test_cpu_request_uses_production_backend_and_preserves_parent_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            weight = root / "model with spaces.pth"
            weight.touch()
            clip = root / "clip encoder"
            clip.mkdir()
            output = root / "results"

            def backend(command, **options):
                self.assertEqual(command[:3], [sys.executable, "-B", str(infer.ROOT / "backend_cli.py")])
                self.assertEqual(options["cwd"], infer.ROOT)
                self.assertEqual(options["env"]["TEXT2REVIT_DEVICE"], "cpu")
                self.assertEqual(options["env"]["TEXT2REVIT_CHECKPOINT"], str(weight.resolve()))
                self.assertEqual(options["env"]["TEXT2REVIT_CLIP_DIR"], str(clip.resolve()))
                self.assertEqual(options["env"]["MPLBACKEND"], "Agg")
                self.assertEqual(options["env"]["PATH"].split(os.pathsep)[0],
                                 str(Path(sys.executable).resolve().parent))
                request = Path(command[command.index("--request") + 1])
                self.assertEqual(json.loads(request.read_text()),
                                 {"prompt": "A small 2-bedroom apartment with 1 bathroom and 1 balcony.",
                                  "seed": 42, "language": "zh"})
                response = Path(command[command.index("--response") + 1])
                response.write_text("{}")
                response.with_suffix(".png").write_bytes(b"preview")
                return subprocess.CompletedProcess(command, 0)

            with patch.dict(os.environ, {"TEXT2REVIT_DEVICE": "parent-value"}), \
                    patch.object(infer.subprocess, "run", side_effect=backend), redirect_stdout(StringIO()):
                code = infer.main(["--prompt", "A small 2-bedroom apartment with 1 bathroom and 1 balcony.",
                                   "--checkpoint", str(weight), "--clip-dir", str(clip), "--device", "cpu",
                                   "--seed", "42", "--language", "zh", "--output-dir", str(output)])
                self.assertEqual(os.environ["TEXT2REVIT_DEVICE"], "parent-value")
            self.assertEqual(code, 0)
            self.assertEqual({p.suffix for p in output.iterdir()}, {".json", ".png"})

    def test_backend_failure_is_reported_and_temporary_request_is_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            def backend(command, **options):
                self.assertNotIn("TEXT2REVIT_DEVICE", options["env"])
                return subprocess.CompletedProcess(command, 7)
            with patch.dict(os.environ, {"TEXT2REVIT_DEVICE": "cpu"}), \
                    patch.object(infer.subprocess, "run", side_effect=backend):
                code = infer.main(["--prompt", "A 3-bedroom apartment with 2 bathrooms and 1 balcony.",
                                   "--output-dir", directory])
            self.assertEqual(code, 7)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_missing_explicit_checkpoint_fails_before_starting_backend(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(infer.subprocess, "run") as backend:
            with self.assertRaises(SystemExit) as error, patch("sys.stderr", StringIO()):
                infer.main(["--prompt", "A 3-bedroom apartment with 2 bathrooms and 1 balcony.",
                            "--checkpoint", str(Path(directory) / "missing.pth")])
            self.assertEqual(error.exception.code, 2)
            backend.assert_not_called()

    def test_help_works_without_loading_model_or_training_libraries(self):
        result = subprocess.run([sys.executable, "-S", "-B", str(infer.ROOT / "infer.py"), "--help"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--checkpoint", result.stdout)
        self.assertIn("--device", result.stdout)


if __name__ == "__main__":
    unittest.main()
