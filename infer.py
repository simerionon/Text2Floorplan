"""Generate a floor-plan PNG and editable JSON without Revit or a browser.

Example: python infer.py --prompt "A 3-bedroom apartment with 2 bathrooms and 1 balcony."
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True, help="Supported English apartment prompt")
    parser.add_argument("--checkpoint", type=Path, help="Full or inference-only Flow Matching PTH")
    parser.add_argument("--clip-dir", type=Path, help="Local CLIP text encoder directory")
    parser.add_argument("--device", choices=("auto", "cpu"), default="auto",
                        help="Automatically use a compatible GPU, or force CPU")
    parser.add_argument("--seed", type=int, help="Initial generation seed")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "inference")
    parser.add_argument("--language", choices=("en", "zh"), default="en",
                        help="Progress-message language; prompts remain English")
    args = parser.parse_args(argv)
    if not args.prompt.strip():
        parser.error("--prompt must not be empty")
    if args.checkpoint is not None and not args.checkpoint.is_file():
        parser.error(f"Checkpoint does not exist: {args.checkpoint}")
    if args.clip_dir is not None and not args.clip_dir.is_dir():
        parser.error(f"CLIP directory does not exist: {args.clip_dir}")

    output = args.output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    response = output / f"floorplan_{datetime.now():%Y%m%d_%H%M%S_%f}.json"
    environment = os.environ.copy()
    environment.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1",
                       TEXT2REVIT_BACKEND="1", MPLBACKEND="Agg")
    python_home = Path(sys.executable).resolve().parent
    library_paths = [python_home, python_home / "Library" / "bin", python_home / "DLLs"]
    environment["PATH"] = os.pathsep.join(str(p) for p in library_paths if p.is_dir()) + os.pathsep + environment.get("PATH", "")
    if python_home == ROOT / "runtime":
        # Match the portable launcher's isolated runtime when invoked directly.
        environment.pop("PYTHONHOME", None)
        environment.pop("PYTHONPATH", None)
        environment["PYTHONNOUSERSITE"] = "1"
    if args.device == "cpu":
        environment["TEXT2REVIT_DEVICE"] = "cpu"
    else:
        environment.pop("TEXT2REVIT_DEVICE", None)
    for value, variable in ((args.checkpoint, "TEXT2REVIT_CHECKPOINT"),
                            (args.clip_dir, "TEXT2REVIT_CLIP_DIR")):
        if value is not None:
            environment[variable] = str(value.resolve())

    # Reuse the production backend's geometry checks, retries and GPU fallback.
    # The request is temporary; the result JSON retains the prompt and final seed.
    with tempfile.TemporaryDirectory(prefix=".request-", dir=output) as directory:
        request = Path(directory) / "request.json"
        request.write_text(json.dumps({"prompt": args.prompt, "seed": args.seed,
                                       "language": args.language}, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(ROOT / "backend_cli.py"),
                                 "--request", str(request), "--response", str(response)],
                                cwd=ROOT, env=environment, check=False)
    if result.returncode:
        return result.returncode
    print(f"JSON: {response}")
    print(f"PNG:  {response.with_suffix('.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
