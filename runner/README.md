# Runner

A small Python HTTP server (`runner/main.py`, stdlib only) that runs the coding agent for one issue at a time. n8n calls it to start a run and to poll the result.

Per run it creates a git worktree `runner/worktrees/issue-N` on branch `issue-N`, builds the prompt from `prompts/agent.md`, and runs `claude -p` (Sonnet). It then reads the agent's final JSON status block and pushes the branch. Only one run is active at a time.

## Start

```bash
scripts/start-runner.sh
```

Keep the terminal open. The script refuses to start if port 8787 is taken, runs `git pull --ff-only`, then starts `python3 runner/main.py`. From n8n in Docker the runner is at `http://host.docker.internal:8787`.

## API

| Endpoint | Description |
| --- | --- |
| `POST /runs` | Start a run. Body: JSON with `issue` (required number) and optional `title`, `spec`, `qa`. Returns `202` with `run_id` and `state`, `400` on a bad body, `409` if a run is active. |
| `GET /runs/{id}` | Run state: `state`, `branch`, `summary`, `question`, `tests`, `log_tail`. `404` if unknown. |
| `GET /health` | `200` with `status: ok` |

`state` is `running`, `done`, `question` or `stuck`. A timeout, a non-zero exit, a missing status block or a failed push gives `stuck`.

```bash
curl http://localhost:8787/health
curl -X POST localhost:8787/runs -d '{"issue": 20, "title": "...", "spec": "..."}'
```

## Environment variables

No variable is required. All are optional:

- `RUNNER_PORT`: listen port (default `8787`)
- `RUNNER_TIMEOUT`: seconds before a run is stopped (default `1800`)
- `RUNNER_AGENT_CMD`: replaces `claude -p`; the prompt goes to stdin (used in tests)
- `RUNNER_REPO_ROOT`: repo root (default: parent of `runner/`)
- `RUNNER_WORKTREES_DIR`: worktree folder (default `runner/worktrees`)
- `RUNNER_LOGS_DIR`: log folder (default `runner/logs`)
- `RUNNER_STATE_DIR`: run state folder (default `runner/state`, saved as `runs.json`)
