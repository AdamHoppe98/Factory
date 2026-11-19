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
