from __future__ import annotations

import json
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
HOST = "127.0.0.1"
PORT = 8770


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        clean = path.split("?", 1)[0].lstrip("/")
        target = WEB / (clean or "index.html")
        return str(target.resolve())

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/api/run":
            self._json(404, {"ok": False, "error": "NOT_FOUND"})
            return
        proc = subprocess.run(
            [sys.executable, str(ROOT / "demo_flow.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = (proc.stdout + proc.stderr).strip()
        self._json(
            200 if proc.returncode == 0 else 500,
            {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "output": output,
            },
        )

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    if not WEB.exists():
        raise SystemExit("WEB_DIR_MISSING")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"HERMX ProofGate demo UI: http://{HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
