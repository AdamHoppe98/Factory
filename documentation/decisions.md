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

## 2026-11-24 – T1.3 WF1 Refine
- WF1 polls every minute and refines **one** issue per run: an `Ideas` issue, or a `Ready for approval` issue with a comment from Adam after the latest spec. The oldest issue goes first. Why: Ollama handles one request at a time anyway, and one issue per run keeps the execution log easy to read.
- The label is set to `Refining` before the model runs. A run takes about a minute, and the next poll skips issues in `Refining`, so the same issue isn't refined twice.
- If Ollama fails (after 1 retry), the issue goes back to its old label, and the next poll tries again. `Refining` never gets stuck because of an Ollama error.
- Labels are set with `PUT /issues/N/labels`. It replaces all labels in one call, keeps non-state labels (such as `bug`) and swaps only the state label. The native GitHub node's label field can't build a list from an expression.
- GitHub calls use HTTP Request with the `Github Factory` credential when the GitHub node has no matching operation (listing comments, reading a raw file). Posting the spec uses the native GitHub node.
- The prompt and the template are read from `main` through the GitHub API on every run. A prompt change goes live when Adam merges it, with no re-import in n8n. (Answers the T1.2 question: Adam agreed.)
- The author filter (only `AdamHoppe98` issues and comments) is already in WF1, because it costs one condition. T2.7 still covers the other workflows.
- Adam activates WF1 in n8n. The auto-mode permission check blocked Claude from activating it, which matches the rule that putting a workflow live is Adam's QA step. Claude creates the workflow inactive in n8n, and the JSON goes in by PR.
- Test with issue #3, after Adam activated WF1: `Ideas` → `Refining` → `Ready for approval` with a spec in 42 s (execution 29). Polls with nothing to do take about 1 s (executions 30–32) and don't refine #3 again. A comment from Adam sent #3 back through `Refining`, and the new spec in about 80 s (execution 33) used the comment: tooltip instead of a page, the named WoW API, no saved settings, questions cleared. The run after that did nothing, so there's no loop.
- Spec quality on #3 (report): the first spec planned an `AdamAddonDB` schema change nobody asked for, and its open questions were technical ("which API?"), not questions for Adam. The second spec kept an old test step (`/adam bagspace`) that no longer fit. This matches the T1.2 finding: Adam's review in `Ready for approval` is needed.

## 2026-11-25 – T1.4 WF2 Start task (Basic A)
- WF2 polls every minute. If any open issue is `Building`, it does nothing. Otherwise it takes Adam's oldest `Approved` issue, sets `Building` and posts a `factory:status` comment with the command `scripts/run-manual.sh N` (written in T1.6). Why: the assignment says one task is built at a time, and the oldest goes first, like a queue.
- The label is set before the comment, so the next poll sees `Building` and doesn't start a second task.
- The "only one Building" check counts every open issue, not only Adam's, because the limit is about the machine, not the author.
- A small Code node holds the rule. It needs all issues at once (is anything Building, then sort and take the first), which would otherwise take Filter + Aggregate + IF + Sort + Limit.
- In Basic A, Adam moves the task on by hand after the run (PR → WF3, question → comment and `Approved`, failure → `Stuck`). T2.4 replaces the comment with `POST /runs`.
- Claude doesn't set `Approved`, not even on test issues. The auto-mode permission check blocked it, which enforces the "only Adam approves" rule. Claude creates the test issues, and Adam approves them.
- **Bug found in the WF2 test (WF1, race condition):** WF1 set labels with `PUT`, which replaces all labels with a list read before the model ran. Adam added `Approved` to #5 at 07:34:53 while WF1 was refining it, and at 07:35:01 WF1 overwrote it with `Ready for approval`. (Report: a real race between the human and the factory, found by testing, not by reading the code.)
- Fix in WF1 and WF2: every state change is a guarded move. `DELETE` the old state label, then add the new one only if the old one was there (HTTP 200) and no other state label is set. A label Adam sets during a run always wins. Non-state labels are never touched, so the `otherLabels` snapshot is gone.
- The permission check also blocks Claude from updating a live workflow in n8n. So Claude creates new workflows inactive, and Adam imports changes to existing ones from the PR JSON. That matches the "import is QA" rule.
- WF2 itself worked on its first scheduled run: #6 was the only `Approved` issue, became `Building` and got the run-command comment (execution 69).
- Test after Adam imported the fix: #5 `Approved` stayed waiting while #6 was `Building`. After #6 was closed, #5 became `Building` with the run command within about 60 s. One task at a time works.
- In n8n, the import swapped the IDs: WF1 Refine is now `hlHnpqcmA3FWN14F` and WF2 Start task is `5jO4gJgmN7w72ETv`. Workflows are matched by name, not by ID, so nothing depends on it.

## 2026-11-25 – T1.5 WF3 Track PRs
- WF3 polls every minute and reads three lists: open issues, issues closed in the last 2 days, and open PRs. A Code node joins them by issue number and lists the moves. Each move uses the same guarded label move as WF1 and WF2.
- Closed issue with a state label other than `Done` → `Done`. That covers a merged PR (`Closes #N` closes the issue) and an issue Adam closes himself. The 2-day window keeps the list short, and an issue already at `Done` drops out.
- Open PR from `issue-N` → `Your QA`, but **only from `Building`**, and only if the PR changed after WF2's latest "Building" comment. Why: when Adam sends a task back from `Your QA` to `Approved`, the PR stays open. A plain "open PR → Your QA" rule would undo Adam's choice on the next poll, or skip the rebuild as soon as WF2 starts it.
- A closed PR that wasn't merged changes nothing. The issue stays where it is, and Adam decides (`Approved` to retry, or close the issue).
- The list nodes always output data, so an empty list (for example no open PRs) doesn't stop the run before the `Done` moves.
- Test after Adam activated WF3: the closed test issues #3, #5 and #6 got `Done` on the first run. Test issue #8 (`Building`, via WF2) moved to `Your QA` about 30 s after a PR from `issue-8` was opened (PR #10). The PR was closed without merging, and then #8 was closed. #8 got `Done` within about 50 s.

## 2026-11-25 – T1.6 agent prompt and manual run
- `prompts/agent.md` has `{{ISSUE}}`, `{{TITLE}}`, `{{SPEC}}` and `{{QA}}` placeholders. The runner (T2.2) will fill in the same file, so Basic A and Basic B give the agent the same prompt.
- Agent rules: stay on `issue-N` and don't push (the factory pushes), only change files in the Target, ask with status `question` instead of guessing when it changes what gets built, test the work, and end with the JSON status block from CLAUDE.md.
- There's no Lua interpreter on the Mac, so the prompt tells the agent to reread its Lua changes and list in-game test steps, rather than claim tests it can't run. (Report: AdamAddon QA is mostly manual.)
- `scripts/run-manual.sh N` uses the latest `factory:spec` comment, plus the agent's `factory:question` comments and Adam's comments after it as Q&A. Status comments are left out.
- It runs in a git worktree at `runner/worktrees/issue-N` (git-ignored), the same place the runner will use. Adam's main checkout is never switched to another branch. An existing local or pushed `issue-N` branch is continued, so a task sent back to `Approved` builds on its earlier work.
- Claude Code runs interactively (`claude --model sonnet "<prompt>"`), so in Basic A Adam watches and approves each tool call. Afterwards the script offers to push the branch and open the PR with `Closes #N`, and WF3 then sets `Your QA`.
- Guards: the script refuses an issue that isn't `Building`, or that has no spec. `--dry-run` prints the prompt. Checked on #3 (uses the newer of the two specs, no placeholders left), #3 without dry-run (stopped: not Building) and #8 (stopped: no spec).

## 2026-11-25 – T1.7 questions during a manual run
- First real run (#11): the agent asked a question, and Adam answered it in the Claude Code CLI. That works in Basic A, because the session keeps the context, but the Q&A is then missing from GitHub: no trace for the evaluation, and a later run of the same issue wouldn't know the answer.
- Rule for Basic A: if Adam answers in the CLI, the question is copied to the issue as a `factory:question` comment and the answer as Adam's plain comment, so `run-manual.sh` includes it as Q&A next time. The full loop (`Waiting for you` → comment → `Approved` → new run) is automated in Basic B by WF4 and WF1 v2.
- Bugs in `run-manual.sh` found on the first real run: (1) `gh pr create` failed with "No default remote repository", because Factory has two remotes since the subtree (`origin`, `adamaddon`). Fix: every `gh` call names `--repo AdamHoppe98/Factory`. (2) The commit list was empty, because `git log` opened the pager (`LESS=-R`) and the screen was cleared. Fix: `git --no-pager`. The PR for #11 was opened by hand.

## 2026-11-25 – T1.8 AdamAddon sync Action (new task)
- Question (Adam): pushing addon changes back to AdamAddon is a manual `git subtree push` after every merge. Can it be part of the workflow? Answer: yes, as a GitHub Action, added to the plan as T1.8.
- Why an Action: it runs at the moment that matters (the push to `main` after a merge), needs no laptop or chat, and shows failures as a red ✗. n8n can't do it (Docker, no git). A script would still be a step to forget.
- Never force-push. If AdamAddon has commits Factory doesn't have, the push fails, and Adam runs `git subtree pull` once. New rule: addon changes go through Factory (CLAUDE.md updated). The gaming PC only pulls.
- Token: fine-grained, Contents write on AdamAddon only, stored as the Actions secret `ADAMADDON_TOKEN`. Checkout uses `persist-credentials: false` so the Factory token doesn't override it.
- Checked locally: `git subtree split` of Factory `main` gives `12d5364`, AdamAddon's exact `main`, because the subtree was added without `--squash`. The split of `issue-11` is one new commit on top of it. So the Action's push is a plain fast-forward.
- Run 2 (#12): at the end, the agent said "the PR is ready for merge", but the PR is only created after Claude Code exits and the script pushes. Cause: the prompt said the factory opens the PR, but not when. Fix: `agent.md` now says the PR only exists after the run and must never be called ready. `run-manual.sh` adds a manual-run line that makes the agent end with "Type /exit. The script then pushes issue-N and opens the PR." That line stays out of `agent.md`, because the Basic B runner has no chat. (Report: the agent fills gaps in its context with plausible claims, so the prompt has to state the process explicitly.)
- Runner skeleton (#12): stdlib `http.server` only (no dependencies, Python 3.9). State is saved to `runner/state/runs.json`, created on first write. Runs stay `running` in the skeleton (no execution yet), so on startup any `running` run is marked `stuck`, otherwise a restart would never allow a new run. `POST /runs` takes an optional JSON body with `issue`; branch is `issue-N`. Listens on 127.0.0.1:8787 (Docker Desktop reaches it via `host.docker.internal`).
- T1.8 setup slip: the guide said to run `gh secret set` through Claude Code's `!` prefix. The token was pasted as the secret's name, so GitHub rejected it (422), but the token was then in the chat transcript and had to be regenerated. Guide changed: set secrets in a separate terminal, and paste the value only at the prompt. (Report: secrets and an AI chat need a clear boundary. The guide should never route a secret through the chat.)
- T1.8 test: Adam set `ADAMADDON_TOKEN` in a separate terminal, and Claude started the Action by hand (run 45612022719, green). AdamAddon `main` is now `22f9c55` "Restyle Blizzard chat frames… (#11)", a fast-forward on `12d5364`, and it equals the subtree split of Factory `main`. From now on the Action runs by itself after each merge that touches `projects/AdamAddon`.

## 2026-11-25 – Assignment version 2
- Adam added `Exam.project.description-version.2.md`. Only the Advanced part changed: two required parts (the runner checks the agent's work and tests itself, with a `Flagged` label for changed tests or `.github/`; the agent in a container on a closed network, and only the runner pushes) and a list of extensions (Neo4j memory, MCP `search_past_tasks`, AI review, review comments back to the agent, metrics).
- PLAN Phase 3 updated: T3.1 runner checks and T3.2 container are required tasks. Adam picks the extensions after Basic B, as before.
- No change to the T2.2 issue that is about to be built. Its "no push for the agent" and "configurable agent command" already fit T3.2.
- Open point for T3.1: AdamAddon has no tests and the Mac has no Lua interpreter. The runner needs some check for addon tasks, for example `luac -p` in the container.
- Review of PR #16 (T2.2, built by the factory from #15): 11/11 tests pass. Real smoke run with `claude -p` against a sandbox clone whose `origin` is a local bare repo: `done` in 15 s, file committed by the agent, branch pushed by the runner, JSON status block at the end of the log. `curl` was blocked by the allowlist, and so were shell redirects and chained commands (the agent used the Write tool instead).
- Allowlist gap: `Bash(python3:*)` lets the agent run any Python, including `git push` or network calls through `subprocess`. So the allowlist is not a security boundary, only a guardrail. Narrowing it to test commands is moved to T2.3. The real boundary is the container in T3.2. (Report: a tool allowlist only limits honest mistakes. Isolation needs a sandbox.)
- `claude -p` prints only the final message, so the log is the final answer, not the whole session. Enough for T2.3 parsing. A full transcript (`--output-format stream-json`) can be added later if needed.

## 2026-11-25 – Agents don't edit the shared docs
- Problem: both agent PRs so far (#14, #16) conflicted with `main`, because the agent and the interactive session both append to `decisions.md` (and `PLAN.md`) while the agent's branch is open. GitHub can't merge two appends at the end of the same file.
- Rule (Adam agreed): agent runs don't edit `PLAN.md`, `decisions.md` or `evaluation-log.md`. The agent writes its design decisions in the commit message body, and the review copies them into `decisions.md`. Commit messages survive in both Basic A and B and show up in the PR. The agent's final chat message is lost in Basic A (#11).
- `agent.md` rule 7 and a note at the top of CLAUDE.md's "How we work" section. Without the CLAUDE.md note, the agent would see two rules that contradict each other.
## 2026-11-25 – T2.2 runner execution (#15)
- `POST /runs` returns 400 without a positive numeric `issue`, stores `title`/`spec`/`qa`, then runs the agent in a background thread (202 at once). Run states: `running` → `done` (exit 0 and push ok) or `stuck` (non-zero exit, timeout, worktree or push failure). T2.3 will add `question` parsing.
- Worktree `runner/worktrees/issue-N`: reused if present, else created from local `issue-N`, `origin/issue-N` or `origin/main` (in that order). Prompt comes from `prompts/agent.md`; empty Q&A becomes `None`; the prompt goes to the agent on stdin.
- Agent command: `claude -p --model sonnet --allowedTools ...`, replaced by `TEST_AGENT_CMD` when set (also the hook for T3.2). Timeout `TEST_TIMEOUT`, default 1800 s; on timeout the whole process group is killed. Allowlist: Read/Edit/Write/Glob/Grep and local git (status, diff, log, add, commit, show), ls, mkdir, python. No push, no curl/WebFetch.
- Only the runner pushes (`git push origin issue-N` after exit 0). Log: `runner/logs/issue-N-<run_id>.log`; `log_tail` is its last 30 lines.
