"""Factory runner skeleton: HTTP API with run state.

Endpoints:
  POST /runs        start a run (202 + run_id, 409 if a run is active)
  GET  /runs/{id}   run state, branch, summary, question, tests, log_tail
  GET  /health      200 {"status": "ok"}

A run executes in a background thread: git worktree runner/worktrees/issue-N
on branch issue-N, the prompt from prompts/agent.md, then the agent command
(`claude -p` by default). On exit code 0 the runner reads the last ```json block
in the log: {"status": "done|question|stuck", "summary", "question", "tests"}.
done and question -> branch pushed to origin, state set to the status.
stuck, a missing or invalid block, an unknown status, a non-zero exit, a timeout
or a push failure -> state "stuck".
State lives in memory and is saved to runner/state/runs.json.

Env vars (all optional, defaults in brackets):
  RUNNER_PORT           HTTP port [8787]
  RUNNER_STATE_DIR      folder for runs.json [runner/state]
  RUNNER_AGENT_CMD      replaces `claude -p`, prompt on stdin [unset: `claude -p`]
  RUNNER_TIMEOUT        run timeout in seconds [1800]
  RUNNER_REPO_ROOT      repo the worktrees are made from [parent of runner/]
  RUNNER_WORKTREES_DIR  where worktrees are created [runner/worktrees]
  RUNNER_LOGS_DIR       where run logs are written [runner/logs]
"""
import json
import os
import re
import shlex
import signal
import subprocess
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("RUNNER_PORT", "8787"))
STATE_DIR = os.environ.get(
    "RUNNER_STATE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")
)
ACTIVE_STATES = ("running",)
HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(os.path.dirname(HERE), "prompts", "agent.md")
DEFAULT_TIMEOUT = 30 * 60
LOG_TAIL_LINES = 30
# File operations and local git only. No push, no network (no WebFetch/curl).
ALLOWED_TOOLS = ",".join([
    "Read", "Edit", "Write", "Glob", "Grep",
    "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)",
    "Bash(git add:*)", "Bash(git commit:*)", "Bash(git show:*)",
    "Bash(ls:*)", "Bash(mkdir:*)", "Bash(python3 -m unittest:*)",
])


def repo_root():
    return os.environ.get("RUNNER_REPO_ROOT") or os.path.dirname(HERE)


def build_prompt(run):
    with open(PROMPT_PATH) as f:
        text = f.read()
    values = {
        "ISSUE": str(run["issue"]),
        "TITLE": run["title"],
        "SPEC": run["spec"],
        "QA": run["qa"] or "None",
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), text)


def agent_command():
    cmd = os.environ.get("RUNNER_AGENT_CMD")
    if cmd:
        return shlex.split(cmd)
    return ["claude", "-p", "--model", "sonnet", "--allowedTools", ALLOWED_TOOLS]


def git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def ensure_worktree(issue, path):
    """Reuse an existing worktree, else create it. Returns an error string or None."""
    if os.path.isdir(path):
        return None
    root = repo_root()
    branch = "issue-%s" % issue
    git(["fetch", "origin"], root)  # best effort; offline falls back to local refs
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if git(["rev-parse", "--verify", "--quiet", "refs/heads/" + branch], root).returncode == 0:
        args = ["worktree", "add", path, branch]
    elif git(["rev-parse", "--verify", "--quiet", "origin/" + branch], root).returncode == 0:
        args = ["worktree", "add", "-b", branch, path, "origin/" + branch]
    else:
        base = "origin/main"
        if git(["rev-parse", "--verify", "--quiet", base], root).returncode != 0:
            base = "main"
        args = ["worktree", "add", "-b", branch, path, base]
    r = git(args, root)
    return None if r.returncode == 0 else "git worktree add failed: " + r.stderr.strip()


def tail_of(path, lines=LOG_TAIL_LINES):
    try:
        with open(path, errors="replace") as f:
            return "".join(f.readlines()[-lines:])
    except OSError:
        return ""


JSON_BLOCK = re.compile(r"```json[ \t]*\r?\n(.*?)```", re.DOTALL)
STATUSES = ("done", "question", "stuck")


def parse_status(log_path):
    """Read the last ```json block in the log. Returns a dict with status, summary,
    question, tests. Problems give status "stuck" with the reason as summary."""
    def stuck(summary):
        return {"status": "stuck", "summary": summary, "question": "", "tests": ""}

    try:
        with open(log_path, errors="replace") as f:
            blocks = JSON_BLOCK.findall(f.read())
    except OSError:
        blocks = []
    if not blocks:
        return stuck("No status block found in the agent output.")
    try:
        data = json.loads(blocks[-1])
    except ValueError:
        return stuck("Invalid JSON in the status block.")
    if not isinstance(data, dict):
        return stuck("Invalid JSON in the status block: expected an object.")
    status = data.get("status")
    if status not in STATUSES:
        return stuck("Unknown status %r in the status block." % (status,))
    result = {k: "" if data.get(k) is None else str(data[k]) for k in ("summary", "question", "tests")}
    result["status"] = status
    return result


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

    def update(self, run_id, **fields):
        with self.lock:
            self.runs[run_id].update(fields)
            self._save()

    def create(self, issue, title="", spec="", qa=""):
        """Return the new run, or None if a run is already active."""
        with self.lock:
            if any(r["state"] in ACTIVE_STATES for r in self.runs.values()):
                return None
            run_id = uuid.uuid4().hex[:12]
            run = {
                "run_id": run_id,
                "issue": issue,
                "title": title,
                "spec": spec,
                "qa": qa,
                "state": "running",
                "branch": "issue-%s" % issue,
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


def execute_run(store, run):
    """Run the agent for one run and record the outcome. Never raises."""
    run_id, issue, branch = run["run_id"], run["issue"], run["branch"]
    log_dir = os.environ.get("RUNNER_LOGS_DIR") or os.path.join(HERE, "logs")
    log_path = os.path.join(log_dir, "issue-%s-%s.log" % (issue, run_id))

    def finish(state, summary, **extra):
        store.update(run_id, state=state, summary=summary, log_tail=tail_of(log_path), **extra)

    try:
        os.makedirs(log_dir, exist_ok=True)
        wt_dir = os.environ.get("RUNNER_WORKTREES_DIR") or os.path.join(HERE, "worktrees")
        path = os.path.join(wt_dir, branch)
        err = ensure_worktree(issue, path)
        if err:
            with open(log_path, "w") as f:
                f.write(err + "\n")
            return finish("stuck", err)
        timeout = float(os.environ.get("RUNNER_TIMEOUT") or DEFAULT_TIMEOUT)
        with open(log_path, "w") as log:
            proc = subprocess.Popen(
                agent_command(), cwd=path, stdin=subprocess.PIPE, stdout=log,
                stderr=subprocess.STDOUT, text=True, start_new_session=True,
            )
            threading.Thread(target=_feed, args=(proc, build_prompt(run)), daemon=True).start()
            try:
                code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                log.write("\n[runner] killed after %s seconds\n" % timeout)
                return finish("stuck", "Agent killed after timeout (%s s)." % timeout)
        if code != 0:
            return finish("stuck", "Agent exited with code %s." % code)
        result = parse_status(log_path)
        extra = {"question": result["question"], "tests": result["tests"]}
        if result["status"] == "stuck":
            return finish("stuck", result["summary"], **extra)
        push = git(["push", "origin", branch], path)
        with open(log_path, "a") as log:
            log.write("\n[runner] git push origin %s:\n%s%s" % (branch, push.stdout, push.stderr))
        if push.returncode != 0:
            return finish("stuck", "Agent reported %s but git push failed." % result["status"], **extra)
        finish(result["status"], result["summary"], **extra)
    except Exception as e:  # keep the run from staying "running" forever
        finish("stuck", "Runner error: %s" % e)


def _feed(proc, prompt):
    try:
        proc.stdin.write(prompt)
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        pass


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
        issue = body.get("issue")
        if isinstance(issue, str) and issue.isdigit():
            issue = int(issue)
        if isinstance(issue, bool) or not isinstance(issue, int) or issue < 1:
            return self._send(400, {"error": "issue (positive number) is required"})
        fields = {k: str(body.get(k) or "") for k in ("title", "spec", "qa")}
        run = self.store.create(issue, **fields)
        if run is None:
            return self._send(409, {"error": "a run is already active"})
        threading.Thread(target=execute_run, args=(self.store, run), daemon=True).start()
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
