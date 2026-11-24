# Decisions and Q&A log

Short notes for the final report. Add a line whenever a choice about the factory is made.
Format: date – question / decision – answer – why.

## Planning session 2026-11-19

| # | Question | Answer | Why / notes |
|---|---|---|---|
| Q1 | The assignment says one repo, but the target is the separate AdamAddon repo. How do we handle that? | AdamAddon goes in as a subfolder, `projects/AdamAddon`. | Follows the assignment: one repo, one board for n8n. |
| Q2 | Plain copy or git subtree? | `git subtree`, after Adam pushes the changes from his home PC to AdamAddon. | Keeps history, `git subtree pull` brings in later changes, and `git subtree push` can send merged work back. |
| Q3 | Which model for the AI refinement step? | Ollama `qwen3:8b`, local. | No Anthropic API key yet. Free. Can compare with the Claude API later (report: capability vs cost). |
| Q4 | Coding agent and runner location? | Claude Code (`claude -p`), runner as a Python service on the Mac host. | Reuses the existing login and git credentials. n8n in Docker reaches it at `host.docker.internal`. Docker isolation is an Advanced candidate. |
| Q5 | Agent model and billing? | Sonnet, Claude subscription. | Fast and easy on usage limits. Fits small tasks. |
| Q6 | n8n MCP server? | Its own task (T0.3): a setup guide that Adam follows. | The config can't be copied from the other project. A guide also documents the setup for the report. |
| Q7 | Polling interval? | Every 1 minute. | Fast feedback during demos, and far below GitHub's rate limit. |
| Q8 | Docs language? | English. | Matches the assignment and the code. |

## Design decisions (made by Claude, open to change)

| # | Decision | Why |
|---|---|---|
| D1 | Bot comments carry hidden markers (`<!-- factory:spec -->` and so on). | n8n posts as Adam's account. The marker is how it tells its own comments from Adam's answers. |
| D2 | The refined spec is posted as a comment, and the original issue body is left as written. | Keeps Adam's rough idea visible. The latest spec comment is what the agent gets. |
| D3 | The agent ends every run with a JSON status block (`done`/`question`/`stuck`). | The runner can parse it reliably. The assignment asks for an explicit end state. |
| D4 | Every spec has a `Target:` field (`factory` or `projects/AdamAddon`). | One repo, two projects. Later the runner can enforce a path fence. |
| D5 | The runner uses a git worktree per run and continues an existing `issue-N` branch after a question. | The agent doesn't touch Adam's working copy, and a retry keeps earlier progress. |
| D6 | In Basic B, n8n opens the PR (not the agent). | The assignment says "the factory opens the pull request". The agent then never needs PR rights. |

## 2026-11-19 – Plan approved
Adam approved `PLAN.md`. The only change: T0.3 became a setup guide instead of a copied config.

## 2026-11-19 – T0.2 labels
- Label colors follow the assignment diagram: orange = Adam acts, purple = AI works, pink = n8n moves the task. The script uses `--force`, so it is safe to re-run.
- GitHub's default labels (bug, enhancement, …) are kept. They aren't states, and n8n ignores them.

## 2026-11-19 – T0.3 n8n MCP
- Recommended MCP: the community `n8n-mcp` (npx, n8n API key). It can create and update workflows and knows the n8n node schemas. n8n's built-in MCP (n8n 2.44.4) is documented as an alternative, since it is aimed at running workflows.
- The MCP is added with `claude mcp add --scope local`, so the key stays in `~/.claude.json` and out of the repo.
- Checked: Ollama is reachable from the n8n container at `host.docker.internal:11434` (part of T0.4).
- Problem: the first connect timed out. n8n-mcp prints a telemetry banner on stdout, and the first npx download is slow. Fix: `N8N_MCP_TELEMETRY_DISABLED=true`, and the guide now covers it. (Report: an example of tooling friction.)
- Problem: after the restart the MCP connected, but the health check failed with "SSRF protection: Localhost access is blocked in strict mode". n8n-mcp blocks private addresses by default. Fix: `WEBHOOK_SECURITY_MODE=moderate`, which allows localhost and still blocks other private IPs. We chose it over `permissive` because only localhost is needed. Guide updated. (Report: a second example of tooling friction, where a secure default clashes with a local setup.)
- Verified: `n8n_health_check` is ok (n8n-mcp 2.103.2) and `n8n_list_workflows` works. Adam archived the old workflows from an earlier project, so n8n starts clean for WF1–WF4. n8n's built-in MCP stays unconfigured, since we don't need it.

## 2026-11-19 – T0.4 n8n prerequisites
- GitHub access for n8n uses a fine-grained token limited to `AdamHoppe98/Factory`: Issues and Pull requests read/write, Contents read-only. Why: least privilege. n8n never pushes code (the runner pushes with Adam's own git login), so Contents write isn't needed. `gh auth token` was rejected because it can reach every repo. Guide: `documentation/n8n-github-credential.md`.
- The n8n credential is named `GitHub Factory`. Workflows refer to it by that name, so the token can be rotated without changing any workflow.
- Smoke test (execution 26): a temporary webhook workflow read the Factory issues with the `Github Factory` credential and sent a prompt to `qwen3:8b` at `host.docker.internal:11434`. Ollama answered `OK` in about 6 s, cold start included. Then the workflow was deleted.
- Limit: Factory is a public repo with no issues yet, so the read only proves the token is valid (a bad token gives 401). It doesn't prove the Factory-only scope or the write permissions. The write path still needs a test.
- Tooling note: n8n won't delete an active workflow, so the MCP has to deactivate it first.
- Write test (execution 27): creating the issue worked (#1), but GitHub quietly dropped the `Ideas` label, and the comment failed with 403 "Resource not accessible by personal access token". So the token lacks Issues write on Factory. On a public repo, anyone can open an issue, so the create step proved nothing. #1 was closed by hand with `gh`. (Report: the read test alone would have missed this, so it's worth testing writes explicitly.)
- Adam fixed the token permissions. Rerun (issue #2): n8n created the issue with the `Ideas` label, posted a `factory:status` comment, swapped the label to `Done` and closed the issue. Checked on GitHub with `gh`. The temporary workflow was deleted. T0.4 is done.

## 2026-11-24 – T0.5 AdamAddon subtree
- Added with `git subtree add --prefix=projects/AdamAddon adamaddon main`, without `--squash`, so the addon's full history is kept in Factory (as the plan says). Remote name: `adamaddon`.
- Imported AdamAddon `main` at `12d5364`. The branch `feature/spellpower-tooltip` on AdamAddon was not imported; only `main` counts.
- Sync later with `git subtree pull --prefix=projects/AdamAddon adamaddon main`, and push changes back with `git subtree push`.

## 2026-11-24 – T1.1 spec template and issue template
- Spec sections: Target, Goal, Why, Scope (in/out), Constraints, Acceptance criteria, How to test, Open questions. They cover what the assignment asks for (what, why, constraints, checkable criteria) plus what the agent and Adam's QA need.
- Short Markdown headings with `<placeholders>`, not JSON or YAML. Why: qwen3:8b follows a filled-in example more reliably than a schema, and the same text is easy for Adam to read on GitHub.
- Acceptance criteria are checkboxes that must be yes/no checks. That gives the agent a clear definition of done and gives Adam a QA checklist on the PR.
- "How to test" covers both the agent's tests and Adam's manual check. AdamAddon is a WoW addon and can't run outside the game, so most of its QA is manual.
- "Open questions" lets the AI step ask Adam questions inside the spec comment (assignment step 2). "None" means the spec is ready.
- "Only change files inside the Target" is a fixed constraint in every spec (D4).
- The issue template auto-applies the `Ideas` label, so a new idea enters the factory without a manual label step. Its fields (What, Why, Target) are optional hints. The AI step fills the gaps.

## 2026-11-24 – T1.2 refine prompt
- `prompts/refine.md` holds a `{{SPEC_TEMPLATE}}` placeholder, and the caller fills in `templates/spec-template.md`. The template then lives in one place only.
- The prompt input has three parts: `ISSUE`, `PREVIOUS SPEC` and `COMMENTS`. The same prompt handles the first refine and every re-refine after Adam comments.
- The prompt includes a short description of both projects with hard facts (runner port 8787, the 30-minute limit, the addon's `Features/` layout). Why: in v1, qwen3:8b made up port 8080 for the runner. Once the fact was in the prompt, it used 8787.
- Rule "don't invent facts, write `Assumption:` and ask". Without thinking, qwen3:8b ignored it: a vague idea got "Open questions: None", and it picked a Target without asking.
- Decision: WF1 calls Ollama with `think: true`. It follows the rules better (asks about the target and asks real questions). The cost is about 45–55 s per spec instead of 10–30 s, which is fine with polling every minute. Temperature 0.2.
- Known limit: even with thinking, the model adds small unasked details (data persistence, "existing UI framework"). Adam's review in `Ready for approval` is the control for that. (Report: a small local model needs a human gate. The spec review is where it pays off.)
- `scripts/try-refine.py` runs the prompt outside n8n. It can be reused later to compare qwen3:8b with the Claude API (Phase 3). Results: `documentation/examples/refine-example.md`.

## 2026-11-24 – Commit and push rule
- Adam: interactive Claude sessions may commit and push on their own judgment, `main` included. Why: this is an AI-focused project, and asking every time slows the work down. Factory agent runs still only push `issue-N` branches, and Adam still merges every PR. CLAUDE.md updated.
