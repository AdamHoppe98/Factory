# CLAUDE.md – Factory

Exam project: a small software factory. GitHub issues are the specs, n8n orchestrates, a Python runner starts Claude Code, and Adam reviews every PR.
Full assignment: `Exam.project.description-version.2.md` (version 2 has the detailed Advanced part). Plan and task status: `PLAN.md`.

## How we work (important)
These rules are for interactive sessions with Adam. **Factory agent runs** (`prompts/agent.md`) don't edit `PLAN.md`, `documentation/decisions.md` or `documentation/evaluation-log.md`. They put their decisions in the commit message body, and the review copies them into `decisions.md`.
- **Don't build everything in one go.** Follow `PLAN.md`: one task at a time, in order, and only after the plan is approved.
- When a task starts, mark it `[~]` in `PLAN.md`. When it's done and verified, mark it `[x]`.
- **Log every factory decision** in `documentation/decisions.md` as a short line with the why. It is input for the 5-page report.
- Every task that runs through the factory gets a row in `documentation/evaluation-log.md`.
- Ask Adam before you change architecture or scope. Record the question and the answer in `decisions.md`.
- Write docs, code and comments in English. Keep docs short.

## Architecture (summary)
- **GitHub** `AdamHoppe98/Factory`: issues are tasks and labels are states. All issues live here, including AdamAddon tasks.
- **n8n** runs locally in Docker and polls GitHub every 1 minute. From inside Docker, use `host.docker.internal` for the host, never `localhost`.
- **AI step:** Ollama `qwen3:8b` at `http://host.docker.internal:11434`. The prompt is in `prompts/refine.md`, the template in `templates/spec-template.md`.
- **Runner:** Python on the Mac host, port 8787, in `runner/`. One run at a time, 30-minute timeout, git worktree per run.
- **Coding agent:** `claude -p` with Sonnet (subscription login). The prompt wrapper is in `prompts/agent.md`.
- **Built project:** `projects/AdamAddon/`, a git subtree of `github.com/AdamHoppe98/AdamAddon` (a Lua WoW addon). A GitHub Action pushes it to the AdamAddon repo after every merge (`documentation/adamaddon-sync.md`).

## Conventions
- State labels (exactly one per issue): `Ideas`, `Refining`, `Ready for approval`, `Approved`, `Building`, `Waiting for you`, `Stuck`, `Your QA`, `Done`.
- Only Adam sets `Approved`, with one exception: n8n (WF1b) moves `Waiting for you` → `Approved` when Adam answers the agent's question. n8n sets the other states, except `Ideas`.
- Branch is `issue-N`, and the PR body contains `Closes #N`.
- Bot comments start with a hidden marker: `<!-- factory:spec -->`, `<!-- factory:question -->` or `<!-- factory:status -->`. A comment without a marker is a human comment.
- The latest `factory:spec` comment is the current spec.
- The spec field `Target:` is `factory` or `projects/AdamAddon`. Agents only change files inside the target.
- The agent ends every run with a fenced JSON block: `{"status":"done|question|stuck","summary":"...","question":"...","tests":"..."}`.
- n8n only processes issues and comments written by `AdamHoppe98`.

## n8n workflows
- They live as JSON in `n8n/workflows/`, one file per workflow (WF1 Refine, WF2 Start, WF3 Track PRs, WF4 Collect results).
- Change them in a PR. Adam imports them into n8n by hand after review, and that import is part of QA.
- The n8n MCP server (`.mcp.json`) can be used to build and test workflows. Export the final JSON back into the repo.

## Safety rules
- **Interactive sessions with Adam:** commit and push on your own judgment, `main` included. Don't ask first, and don't report "not pushed". Push when a task is done and verified.
- **Factory agent runs:** work only on branch `issue-N`, never push to `main`. Adam reviews the PR.
- Never merge PRs and never force-push. Adam merges.
- Never commit secrets: no tokens, API keys or n8n credentials. Use env vars. `.env` and local MCP secrets are git-ignored.
- Don't edit `projects/AdamAddon/` outside a task that targets it. Sync it with `git subtree pull`, never by hand-copying files. Addon changes go through Factory, not straight into the AdamAddon repo.
- If something is unclear, ask instead of guessing. That goes for interactive sessions and agent runs alike.
