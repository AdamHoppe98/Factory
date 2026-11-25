import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from main import make_server


def call(base, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


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
        self.srv = Server(self.tmp.name + "/state")  # dir does not exist yet

    def tearDown(self):
        self.srv.stop()
        self.tmp.cleanup()

    def test_health(self):
        self.assertEqual(call(self.srv.base, "GET", "/health")[0], 200)

    def test_start_and_get(self):
        code, body = call(self.srv.base, "POST", "/runs", {"issue": 12})
        self.assertEqual(code, 202)
        code, run = call(self.srv.base, "GET", "/runs/" + body["run_id"])
        self.assertEqual(code, 200)
        for key in ("state", "branch", "summary", "question", "tests", "log_tail"):
            self.assertIn(key, run)
        self.assertEqual(run["branch"], "issue-12")

    def test_conflict_when_active(self):
        self.assertEqual(call(self.srv.base, "POST", "/runs", {})[0], 202)
        self.assertEqual(call(self.srv.base, "POST", "/runs", {})[0], 409)

    def test_unknown_run_404(self):
        self.assertEqual(call(self.srv.base, "GET", "/runs/nope")[0], 404)

    def test_persists_after_restart(self):
        _, body = call(self.srv.base, "POST", "/runs", {"issue": 5})
        self.srv.stop()
        self.srv = Server(self.tmp.name + "/state")
        code, run = call(self.srv.base, "GET", "/runs/" + body["run_id"])
        self.assertEqual(code, 200)
        self.assertEqual(run["issue"], 5)
        self.assertEqual(run["state"], "stuck")  # interrupted by restart
        self.assertEqual(call(self.srv.base, "POST", "/runs", {})[0], 202)


if __name__ == "__main__":
    unittest.main()
