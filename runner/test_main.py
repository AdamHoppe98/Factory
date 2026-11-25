import json
import os
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

from main import make_server, build_prompt

FAKE_AGENT = """#!/bin/sh
# Fake agent. FAKE_MODE: success | fail | timeout
cat > prompt.txt
echo "agent output line"
case "$FAKE_MODE" in
  fail) exit 1 ;;
  timeout) sleep 60 ;;
esac
echo built > built.txt
git add built.txt
git commit -q --allow-empty -m "fake work"
"""


def call(base, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def sh(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


class Server:
    def __init__(self, state_dir):
        self.httpd = make_server(0, state_dir)
        self.base = "http://127.0.0.1:%d" % self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class RunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        # A throwaway repo with a bare "origin", so pushes are real but local.
        self.repo = os.path.join(t, "repo")
        self.origin = os.path.join(t, "origin.git")
        os.makedirs(self.repo)
        sh("git", "init", "-q", "-b", "main", cwd=self.repo)
        sh("git", "config", "user.email", "t@example.com", cwd=self.repo)
        sh("git", "config", "user.name", "Test", cwd=self.repo)
        sh("git", "commit", "-q", "--allow-empty", "-m", "init", cwd=self.repo)
        sh("git", "clone", "-q", "--bare", self.repo, self.origin, cwd=t)
        sh("git", "remote", "add", "origin", self.origin, cwd=self.repo)
        sh("git", "fetch", "-q", "origin", cwd=self.repo)
        agent = os.path.join(t, "fake_agent.sh")
        with open(agent, "w") as f:
            f.write(FAKE_AGENT)
        os.chmod(agent, 0o755)
        self.env = {
            "RUNNER_REPO_ROOT": self.repo,
            "RUNNER_WORKTREES_DIR": os.path.join(t, "worktrees"),
            "RUNNER_LOGS_DIR": os.path.join(t, "logs"),
            "TEST_AGENT_CMD": agent,
            "TEST_TIMEOUT": "30",
            "FAKE_MODE": "success",
            "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        self.saved = {k: os.environ.get(k) for k in self.env}
        os.environ.update(self.env)
        self.srv = Server(t + "/state")  # dir does not exist yet

    def tearDown(self):
        self.srv.stop()
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def wait_done(self, run_id, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            _, run = call(self.srv.base, "GET", "/runs/" + run_id)
            if run["state"] != "running":
                return run
            time.sleep(0.1)
        self.fail("run still running")

    def start(self, **body):
        body.setdefault("issue", 7)
        code, resp = call(self.srv.base, "POST", "/runs", body)
        self.assertEqual(code, 202)
        return resp["run_id"]

    def test_health(self):
        self.assertEqual(call(self.srv.base, "GET", "/health")[0], 200)

    def test_missing_issue_400(self):
        self.assertEqual(call(self.srv.base, "POST", "/runs", {})[0], 400)
        self.assertEqual(call(self.srv.base, "POST", "/runs", {"issue": "abc"})[0], 400)

    def test_start_and_get(self):
        run_id = self.start(issue=12)
        code, run = call(self.srv.base, "GET", "/runs/" + run_id)
        self.assertEqual(code, 200)
        for key in ("state", "branch", "summary", "question", "tests", "log_tail"):
            self.assertIn(key, run)
        self.assertEqual(run["branch"], "issue-12")
        self.wait_done(run_id)

    def test_success_pushes_branch(self):
        run_id = self.start(title="My title", spec="My spec")
        run = self.wait_done(run_id)
        self.assertEqual(run["state"], "done", run)
        self.assertIn("agent output line", run["log_tail"])
        wt = os.path.join(self.env["RUNNER_WORKTREES_DIR"], "issue-7")
        self.assertTrue(os.path.isdir(wt))
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=wt,
                                capture_output=True, text=True).stdout.strip()
        self.assertEqual(branch, "issue-7")
        log = os.path.join(self.env["RUNNER_LOGS_DIR"], "issue-7-%s.log" % run_id)
        self.assertIn("agent output line", open(log).read())
        remote = subprocess.run(["git", "branch", "--list", "issue-7"], cwd=self.origin,
                                capture_output=True, text=True).stdout
        self.assertIn("issue-7", remote)
        prompt = open(os.path.join(wt, "prompt.txt")).read()
        self.assertIn("Issue #7: My title", prompt)
        self.assertIn("My spec", prompt)

    def test_failure_is_stuck_and_not_pushed(self):
        os.environ["FAKE_MODE"] = "fail"
        run = self.wait_done(self.start())
        self.assertEqual(run["state"], "stuck")
        remote = subprocess.run(["git", "branch", "--list", "issue-7"], cwd=self.origin,
                                capture_output=True, text=True).stdout
        self.assertEqual(remote.strip(), "")

    def test_timeout_kills_agent(self):
        os.environ["FAKE_MODE"] = "timeout"
        os.environ["TEST_TIMEOUT"] = "1"
        start = time.time()
        run = self.wait_done(self.start())
        self.assertLess(time.time() - start, 20)
        self.assertEqual(run["state"], "stuck")
        self.assertIn("timeout", run["summary"])

    def test_conflict_when_active(self):
        os.environ["FAKE_MODE"] = "timeout"
        os.environ["TEST_TIMEOUT"] = "2"
        run_id = self.start()
        self.assertEqual(call(self.srv.base, "POST", "/runs", {"issue": 8})[0], 409)
        self.wait_done(run_id)

    def test_worktree_reused(self):
        self.wait_done(self.start())
        run = self.wait_done(self.start())  # second run, same issue
        self.assertEqual(run["state"], "done", run)

    def test_unknown_run_404(self):
        self.assertEqual(call(self.srv.base, "GET", "/runs/nope")[0], 404)

    def test_prompt_qa_defaults_to_none(self):
        base = {"issue": 3, "title": "T", "spec": "S"}
        self.assertIn("### Questions and answers since the spec\nNone", build_prompt(dict(base, qa="")))
        self.assertIn("Use blue.", build_prompt(dict(base, qa="Use blue.")))

    def test_persists_after_restart(self):
        os.environ["FAKE_MODE"] = "timeout"
        os.environ["TEST_TIMEOUT"] = "2"
        run_id = self.start(issue=5)
        self.srv.stop()
        self.srv = Server(self.tmp.name + "/state")
        code, run = call(self.srv.base, "GET", "/runs/" + run_id)
        self.assertEqual(code, 200)
        self.assertEqual(run["issue"], 5)
        self.assertEqual(run["state"], "stuck")  # interrupted by restart
        time.sleep(2.5)  # let the orphaned thread finish before cleanup
