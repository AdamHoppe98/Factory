# Factory – Plan

Status: **APPROVED 2026-11-19.** Implement one task at a time.

Source documents: [Exam.project.description-version.2.md](Exam.project.description-version.2.md) (current; v1: [Exam.project.description.md](Exam.project.description.md)), [alreadySetup.md](alreadySetup.md).
Questions, answers and decisions: [documentation/decisions.md](documentation/decisions.md).

## 1. Goal

A small software factory in this repo:

1. Adam writes a rough task as a GitHub issue.
2. n8n refines it with a local LLM.
3. Adam approves it.
4. Claude Code builds it on branch `issue-N`.
5. Adam reviews the pull request.

The factory works on itself and on AdamAddon, a Lua WoW addon that lives in `projects/AdamAddon/`.

## 2. Architecture

```
GitHub (Factory repo)  <-- poll every 1 min -->  n8n (Docker)  --HTTP-->  Runner (Python, on Mac)  -->  claude -p (Sonnet)
 issues = specs                                  orchestrator              host.docker.internal:8787     works in git worktree
 labels = state                                  AI step: Ollama qwen3:8b  one task at a time            on branch issue-N
 comments = Q&A                                  (host.docker.internal:11434)
 PRs = results
```

| Part | Choice | Why (short) |
|---|---|---|
| Task board | GitHub Issues + labels in `AdamHoppe98/Factory` | Required by the assignment. n8n's GitHub node can set labels. |
| Orchestrator | n8n, local Docker | Already set up. Polls GitHub, because GitHub can't reach the laptop. |
| AI step | Ollama `qwen3:8b` | No Anthropic API key yet. Free and local. Claude API is an option later. |
| Coding agent | Claude Code headless (`claude -p`), Sonnet, subscription login | Already available. Sonnet is fast and easy on usage limits. |
| Runner | Python HTTP service on the Mac host | Simplest way to use the existing `claude` login and git credentials. |
| Built project | `projects/AdamAddon/` via `git subtree` | One repo and one board, as the assignment requires. History is kept, and changes can be pushed back. |

## 3. Repo layout

```
CLAUDE.md                     rules for every Claude session
PLAN.md                       this file (plan + task status)
documentation/
  decisions.md                Q&A + decision log (input for the report)
  evaluation-log.md           one entry per task run through the factory
  report/                     the final report (at the end)
templates/spec-template.md    the fixed specification template
prompts/
  refine.md                   system prompt for the n8n AI step
  agent.md                    prompt wrapper the runner gives Claude Code
n8n/workflows/*.json          exported n8n workflows (changed by PR, imported by hand)
runner/                       Python runner + tests
scripts/                      setup-labels.sh, helpers
.github/ISSUE_TEMPLATE/idea.md
projects/AdamAddon/           git subtree of github.com/AdamHoppe98/AdamAddon
```

## 4. Factory conventions

- **Labels (state):** `Ideas`, `Refining`, `Ready for approval`, `Approved`, `Building`, `Waiting for you`, `Stuck`, `Your QA`, `Done`. An issue has exactly one state label at a time.
- **Branch:** `issue-N`. The PR body contains `Closes #N`.
- **Bot comments** start with a hidden marker, for example `<!-- factory:spec -->`, `<!-- factory:question -->` or `<!-- factory:status -->`. n8n uses the same GitHub account as Adam, so the marker is how it tells its own comments apart from a human answer.
- **Refined spec:** the latest `<!-- factory:spec -->` comment on the issue is the spec. The original issue body is left untouched.
- **Target:** every spec has a `Target:` field, either `factory` (repo root) or `projects/AdamAddon`. The agent only changes files inside the target.
- **Agent status contract:** the agent ends every run with a fenced JSON block:
  `{"status": "done|question|stuck", "summary": "...", "question": "...", "tests": "..."}`.
- **Only Adam's tasks:** n8n ignores issues and comments that `AdamHoppe98` didn't write.

## 5. Runner API (Basic B)

| Method | Path | Behavior |
|---|---|---|
| `POST` | `/runs` | Body `{issue, title, spec, qa}`. Returns `202 {run_id}` right away, or `409` if a run is already active. |
| `GET` | `/runs/{id}` | Returns `{state: running\|done\|question\|stuck, branch, summary, question, tests, log_tail}`. |
| `GET` | `/health` | Returns `200`. |

In the background, a run:

1. Creates a git worktree on `issue-N`. If the branch already exists, it continues from it.
2. Runs `claude -p` with `prompts/agent.md`, the spec and the Q&A so far, using a permission allowlist.
3. Kills the agent after 30 minutes. The run is then `stuck`.
4. Parses the status JSON. If the status is `done`, it pushes the branch.

## 6. n8n workflows

| # | Workflow | Moves |
|---|---|---|
| WF1 | Refine | `Ideas`→`Refining`→(AI)→`Ready for approval`. A new human comment moves `Ready for approval` back to `Refining`. In Basic B, `Waiting for you`→`Approved`. |
| WF2 | Start task | `Approved`→`Building`, only if nothing else is `Building`. Basic A: posts the "run it by hand" command. Basic B: `POST /runs`. |
| WF3 | Track PRs | An open PR from `issue-N` moves the issue to `Your QA`. A merged PR or closed issue moves it to `Done`. |
| WF4 | Collect results (B) | Polls `/runs`. `done` → open the PR, `Your QA`. `question` → comment, `Waiting for you`. `stuck` → comment, `Stuck`. |

## 7. Tasks

Work one task at a time. Mark each task done here and log its decisions in `documentation/decisions.md`.
Status: `[ ]` todo, `[~]` in progress, `[x]` done.

### Phase 0 – Setup
- [x] **T0.1** Create the repo skeleton (folders above), `.gitignore`, a README stub and the first commit.
- [x] **T0.2** Write `scripts/setup-labels.sh` to create the 9 state labels with `gh`. Run it.
- [x] **T0.3** Write `documentation/n8n-mcp-setup.md`, a step-by-step guide for adding the n8n MCP server to Claude Code in this project (n8n API key, `claude mcp add`, keep secrets out of git, verify it can list workflows). Adam follows the guide.
- [x] **T0.4** n8n prerequisites: a GitHub credential in n8n, and Ollama reachable from n8n at `host.docker.internal:11434`. Run a smoke test.
- [x] **T0.5** Add AdamAddon as a subtree in `projects/AdamAddon`.

### Phase 1 – Basic A (manual factory)
- [x] **T1.1** Write `templates/spec-template.md` and `.github/ISSUE_TEMPLATE/idea.md`.
- [x] **T1.2** Write `prompts/refine.md`. Test it against qwen3:8b on 2–3 sample ideas outside n8n, and save one example output for the report.
- [x] **T1.3** Build WF1 Refine. Export it to `n8n/workflows/`.
- [x] **T1.4** Build WF2 Start task (Basic A version: sets `Building` and posts the manual command).
- [x] **T1.5** Build WF3 Track PRs.
- [x] **T1.6** Write `prompts/agent.md` and `scripts/run-manual.sh <issue>`, which creates the branch and starts Claude Code with the spec.
- [x] **T1.7** Run 2–3 real tasks end to end, for example T2.1 built by the factory. Log each run in `evaluation-log.md`.
- [x] **T1.8** GitHub Action `sync-adamaddon.yml`: after a merge to `main` that changes `projects/AdamAddon/**`, push the subtree to the AdamAddon repo. *Added 2026-11-25 by Adam's request.*

### Phase 2 – Basic B (automated factory)
- [x] **T2.1** Runner skeleton: HTTP API, in-memory and JSON-file run state, one run at a time, tests.
- [x] **T2.2** Runner execution: git worktree, `claude -p` with an allowlist, 30-minute timeout, branch push. Also from the #12 review: store `title`/`spec`/`qa` on `POST /runs`, and return 400 when `issue` is missing.
- [ ] **T2.3** Runner result parsing for the status contract, plus tests with fake agent output. Also from the #15 review: narrow `Bash(python3:*)`/`Bash(python:*)` in the allowlist to test commands (`python3 -m unittest`), since `python3 -c` can push or reach the network; rename `TEST_AGENT_CMD`/`TEST_TIMEOUT` to `RUNNER_AGENT_CMD`/`RUNNER_TIMEOUT`.
- [x] **T2.4** WF2 v2: call `POST /runs`.
- [x] **T2.5** WF4: collect results and open the PR, or post the question, or mark the task Stuck.
- [x] **T2.6** WF1 v2: `Waiting for you` → `Approved` on Adam's answer. Pass the Q&A to the next run.
- [x] **T2.7** Author filter: only Adam's issues and comments are processed.
- [ ] **T2.8** Run real tasks through the automated factory, both factory tasks and AdamAddon tasks. Log them.

### Phase 3 – Advanced (assignment version 2)
Required, in this order, after Basic B:
- [ ] **T3.1** Runner checks the agent's work: is there a code change, and do the tests pass when the runner runs them? If not → `Stuck`. The real test result goes into the PR. A PR that changes existing tests or `.github/` gets the label `Flagged` and a warning. Open point: AdamAddon has no tests (syntax check such as `luac -p` in the container?).
- [ ] **T3.2** Safe agent: the agent runs in its own container on a closed Docker network that reaches only the model. Only the runner holds the GitHub token and pushes. (The runner's configurable agent command from T2.2 is where this plugs in.)

Extensions: Adam picks after Basic B.
- Memory in Neo4j (n8n reads and writes it; vector search and graph; the refine step uses it).
- MCP tool `search_past_tasks` for the agent (n8n MCP Server Trigger, with authentication).
- AI review of each PR against the acceptance criteria (a different model if possible; advisory only).
- Review comments back to the agent (sent back from `Your QA`, the agent continues on the same branch).
- Metrics: done on the first run, questions, stuck, time per task.

### Phase 4 – Evaluation and report
- [ ] **T4.1** Run several AdamAddon tasks.
- [ ] **T4.2** Write the evaluation (where it worked, where it stopped, where Adam stepped in) from `evaluation-log.md`.
- [ ] **T4.3** Write the report (max 5 pages) in `documentation/report/`.

## 8. Open points
- The Phase 3 extensions get picked after Basic B works. T3.1 and T3.2 are required.
