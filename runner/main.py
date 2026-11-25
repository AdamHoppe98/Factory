"""Factory runner skeleton: HTTP API with run state.

Endpoints:
  POST /runs        start a run (202 + run_id, 409 if a run is active)
  GET  /runs/{id}   run state, branch, summary, question, tests, log_tail
  GET  /health      200 {"status": "ok"}

Skeleton only: no git worktree and no Claude Code yet. A started run stays
"running". State lives in memory and is saved to runner/state/runs.json.
"""
import json
import os
import re
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("RUNNER_PORT", "8787"))
STATE_DIR = os.environ.get(
    "RUNNER_STATE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
)
ACTIVE_STATES = ("running",)


class RunStore:
    """In-memory runs, saved to a JSON file after every change."""

    def __init__(self, state_dir):
        self.path = os.path.join(state_dir, "runs.json")
        self.lock = threading.Lock()
        self.runs = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        with open(self.path) as f:
            self.runs = json.load(f).get("runs", {})
        # A restart killed whatever was running; don't block new runs forever.
        for run in self.runs.values():
            if run["state"] in ACTIVE_STATES:
                run["state"] = "stuck"
                run["summary"] = "Runner restarted while this run was active."
        self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"runs": self.runs}, f, indent=2)
        os.replace(tmp, self.path)

    def create(self, issue):
        """Return the new run, or None if a run is already active."""
        with self.lock:
            if any(r["state"] in ACTIVE_STATES for r in self.runs.values()):
                return None
            run_id = uuid.uuid4().hex[:12]
            run = {
                "run_id": run_id,
                "issue": issue,
                "state": "running",
                "branch": "issue-%s" % issue if issue is not None else "",
                "summary": "",
                "question": "",
                "tests": "",
                "log_tail": "",
            }
            self.runs[run_id] = run
            self._save()
            return dict(run)

    def get(self, run_id):
        with self.lock:
            run = self.runs.get(run_id)
            return dict(run) if run else None


class Handler(BaseHTTPRequestHandler):
    store = None  # set in make_server

    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"status": "ok"})
        m = re.fullmatch(r"/runs/([^/]+)", self.path)
        if m:
            run = self.store.get(m.group(1))
            if run:
                return self._send(200, run)
            return self._send(404, {"error": "run not found"})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/runs":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw) if raw.strip() else {}
        except ValueError:
            return self._send(400, {"error": "body must be JSON"})
        if not isinstance(body, dict):
            return self._send(400, {"error": "body must be a JSON object"})
        run = self.store.create(body.get("issue"))
        if run is None:
            return self._send(409, {"error": "a run is already active"})
        self._send(202, {"run_id": run["run_id"], "state": run["state"]})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


def make_server(port=PORT, state_dir=STATE_DIR):
    handler = type("BoundHandler", (Handler,), {"store": RunStore(state_dir)})
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


if __name__ == "__main__":
    server = make_server()
    print("runner listening on http://127.0.0.1:%d" % server.server_address[1])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
