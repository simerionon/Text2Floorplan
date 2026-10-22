"""Run the local editor: python -m web_editor.server --open."""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import threading
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from web_editor.model_document import apply_command, import_document

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"


class EditorServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, options):
        super().__init__(address, Handler)
        self.options, self.jobs, self.lock = options, {}, threading.Lock()

    def generate(self, job_id, prompt, language):
        job = self.jobs[job_id]
        folder = ROOT / "outputs" / "web_editor" / job_id
        try:
            folder.mkdir(parents=True)
            request, response = folder / "request.json", folder / "plan.json"
            request.write_text(json.dumps({"prompt": prompt, "language": language}), encoding="utf-8")
            job["folder"] = folder
            environment = os.environ.copy()
            environment["PYTHONIOENCODING"] = "utf-8"
            for option, name in (("checkpoint", "TEXT2REVIT_CHECKPOINT"), ("clip_dir", "TEXT2REVIT_CLIP_DIR")):
                if getattr(self.options, option):
                    environment[name] = str(Path(getattr(self.options, option)).resolve())
            with (folder / "inference.log").open("w", encoding="utf-8") as log:
                with self.lock:
                    if job["state"] == "cancelled":
                        return
                    process = subprocess.Popen([self.options.python, str(ROOT / "backend_cli.py"),
                        "--request", str(request), "--response", str(response),
                        "--status", str(folder / "status.json")], cwd=ROOT, env=environment,
                        stdout=log, stderr=subprocess.STDOUT, shell=False)
                    job["process"] = process
                code = process.wait()
            with self.lock:
                if job["state"] == "cancelled":
                    return
            if code:
                lines = (folder / "inference.log").read_text(encoding="utf-8").strip().splitlines()
                raise ValueError(lines[-1][:500] if lines else "Local inference did not finish")
            result = import_document(json.loads(response.read_text(encoding="utf-8")))
            with self.lock:
                if job["state"] != "cancelled":
                    job.update(state="complete", plan=result)
        except Exception as error:
            with self.lock:
                if job["state"] != "cancelled":
                    job.update(state="failed", error=str(error))


class Handler(BaseHTTPRequestHandler):
    def reply(self, data, status=200, mime="application/json"):
        payload = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8") if mime == "application/json" else data
        self.send_response(status)
        self.send_header("Content-Type", mime + ("; charset=utf-8" if mime.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def local_request(self):
        expected = f"127.0.0.1:{self.server.server_port}"
        return self.headers.get("Host") == expected and self.headers.get("Origin", f"http://{expected}") == f"http://{expected}"

    def do_GET(self):
        if not self.local_request():
            return self.reply({"error": "Use the localhost editor URL"}, 403)
        path = urlsplit(self.path).path
        if path == "/api/sample":
            return self.reply(import_document(json.loads((ROOT / "sample" / "plan.json").read_text(encoding="utf-8"))))
        if path.startswith("/api/jobs/"):
            with self.server.lock:
                job = self.server.jobs.get(path.rsplit("/", 1)[-1])
                if not job:
                    return self.reply({"error": "Unknown job"}, 404)
                result = {key: value for key, value in job.items() if key not in {"process", "folder"}}
                status = job.get("folder", Path("/nonexistent")) / "status.json"
                if status.is_file():
                    try:
                        result["message"] = json.loads(status.read_text(encoding="utf-8"))["message"]
                    except (ValueError, OSError):
                        pass
            return self.reply(result)
        target = (STATIC / ("index.html" if path in {"/", "/en", "/zh", "/en/", "/zh/"}
                            else path.lstrip("/"))).resolve()
        if not target.is_relative_to(STATIC.resolve()) or not target.is_file():
            return self.reply({"error": "Not found"}, 404)
        mime = {".js": "text/javascript", ".css": "text/css", ".html": "text/html"}.get(target.suffix, mimetypes.guess_type(str(target))[0] or "application/octet-stream")
        return self.reply(target.read_bytes(), mime=mime)

    def do_POST(self):
        if not self.local_request() or self.headers.get("X-Text2Revit-Editor") != "1":
            return self.reply({"error": "Local editor request required"}, 403)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 2_000_000:
                return self.reply({"error": "Document size must be below 2 MB"}, 413)
            body = json.loads(self.rfile.read(size))
            path = urlsplit(self.path).path
            if path == "/api/import":
                return self.reply(import_document(body["plan"]))
            if path == "/api/edit":
                return self.reply(apply_command(body["plan"], body["command"]))
            if path == "/api/generate":
                prompt = body["prompt"]
                if not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 1000:
                    raise ValueError("Enter a supported apartment prompt")
                with self.server.lock:
                    if any(job["state"] == "running" for job in self.server.jobs.values()):
                        return self.reply({"error": "An inference job is already running"}, 409)
                    job_id = uuid.uuid4().hex
                    self.server.jobs[job_id] = {"state": "running", "message": "Starting local inference…"}
                threading.Thread(target=self.server.generate, args=(job_id, prompt, body.get("language", "en")), daemon=True).start()
                return self.reply({"job_id": job_id}, 202)
            if path.startswith("/api/jobs/") and path.endswith("/cancel"):
                with self.server.lock:
                    job = self.server.jobs.get(path.split("/")[-2])
                    if not job:
                        return self.reply({"error": "Unknown job"}, 404)
                    if job["state"] == "running":
                        job["state"] = "cancelled"
                        process = job.get("process")
                        if process and process.poll() is None:
                            process.terminate()
                return self.reply({"state": job["state"]})
            return self.reply({"error": "Unknown operation"}, 404)
        except (ValueError, KeyError, TypeError, IndexError, StopIteration) as error:
            return self.reply({"error": str(error) or "The selected element no longer exists"}, 400)

    def log_message(self, format, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--language", choices=["en", "zh"], default="en")
    parser.add_argument("--python", default=sys.executable, help="Python with inference dependencies")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--clip-dir", type=Path)
    options = parser.parse_args()
    # Reuse an existing Text2Revit installation's local models when available.
    local_data = os.environ.get("LOCALAPPDATA")
    releases = Path(local_data) / "Text2Revit" / "releases" if local_data else None
    installed = sorted((p for p in releases.iterdir() if (p / "installed.txt").is_file()),
                       key=lambda p: p.stat().st_mtime, reverse=True) if releases and releases.is_dir() else []
    if options.clip_dir is None and not (ROOT / "models" / "clip").is_dir():
        options.clip_dir = next((p / "models" / "clip" for p in installed
                                 if (p / "models" / "clip").is_dir()), None)
    if options.checkpoint is None and not (ROOT / "checkpoints" / "flow_matching_best.pth").is_file():
        options.checkpoint = next((p / "models" / "flow_matching_best.pth" for p in installed
                                   if (p / "models" / "flow_matching_best.pth").is_file()), None)
    server = EditorServer(("127.0.0.1", options.port), options)
    url = f"http://127.0.0.1:{server.server_port}/{options.language}"
    print(f"Text2Floorplan: {url}", flush=True)
    if options.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        with server.lock:
            for job in server.jobs.values():
                process = job.get("process")
                if process and process.poll() is None:
                    process.terminate()
        server.server_close()


if __name__ == "__main__":
    main()
