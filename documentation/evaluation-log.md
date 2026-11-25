# Evaluation log

One entry per task that goes through the factory. This is the raw material for the evaluation section of the report.

| Date | Issue | Target | Basic A/B | Result (merged / sent back / stuck / dropped) | Questions asked | Where Adam stepped in | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-25 | #11 Chat window styling | projects/AdamAddon | A | Merged (PR #13) | 1 by the agent (2 parts): restyle Blizzard's chat frames or build a new window? Background and font too? | Corrected spec 1 by comment. Approved spec 2 although it was still partly wrong. Answered the agent in the CLI. PR opened by hand (script bug). | Spec quality poor, agent caught it. See details. |
| 2026-11-25 | #12 Runner skeleton (T2.1) | factory | A | Merged (PR #14) | 0 by the agent. The spec had 3 open questions, unanswered. | Approved without answering the spec questions. Merge conflict in `decisions.md` fixed by Claude during review. | First factory task built by the factory. See details. |

## Details

### #11 – Chat window styling (AdamAddon)
- **Timeline:** Ideas 09:48 → spec 1 at 09:49 (46 s) → Adam's comment → spec 2 at 09:53 (40 s) → Approved 09:59 → Building 09:59 (WF2, 16 s) → Your QA 10:19 → merged and Done 10:21.
- **Spec (qwen3:8b):** misread the idea twice. Spec 1 removed the 1px outline, the opposite of what Adam wanted. After Adam's comment, spec 2 fixed the goal but kept an acceptance criterion with the same mistake ("no 1px black outline remains"), invented `/adam chat`, and repeated an open question. Adam approved it anyway.
- **Agent (Claude Sonnet):** didn't build the wrong thing. It searched the addon, found no chat window and no `/adam chat`, and stopped with status `question`, giving the two possible readings. After Adam's answer it built `Features/Chat.lua` (208 lines) and one `.toc` line, inside the Target only. The final JSON block was printed but not saved.
- **Adam stepped in:** 1 spec comment, approval, 1 answer in the CLI (copied to the issue afterwards), and the run was started by hand (Basic A).
- **Factory problems found:** `run-manual.sh` couldn't open the PR (`gh` had no default repo, since Factory has two remotes) and showed an empty commit list (`git log` pager). Both fixed in `fa5af43`. The addon repo isn't updated after a merge, so the AdamAddon sync Action was added (T1.8).
- **Takeaway:** the human gate on the spec failed once here (a wrong criterion was approved), and the agent's "ask instead of guessing" rule caught it. Two safety nets, and the second one worked.

### #12 – Runner skeleton (factory, T2.1)
- **Timeline:** Ideas 09:50 → spec at 09:51 (45 s) → Approved 09:59 → waited in Approved while #11 was Building → Building 10:19 (WF2 queue) → Your QA 11:59 → merged and Done 12:04.
- **Spec (qwen3:8b):** good this time. The detailed idea (API copied from PLAN.md) gave a matching spec. Its 3 open questions weren't needed: the agent decided them itself and logged the choices in `decisions.md`.
- **Agent:** stdlib `http.server`, state in `runner/state/runs.json`, 5 unit tests. A good choice it made without being asked: on restart, a `running` run becomes `stuck`, so a crash can't block the factory. At the end it said "the PR is ready for merge" before the PR existed. Fixed in the prompt (`fb74714`).
- **Review (Claude, for Adam):** 5/5 tests pass. Live API test passed: 202/409, run state, restart. n8n reaches the runner from Docker via `host.docker.internal`, even though it listens on 127.0.0.1. Minor gaps moved to T2.2: `POST /runs` doesn't store `title`/`spec`/`qa`, and it accepts a missing `issue`.
- **Adam stepped in:** approval, run started by hand, merge. The script fix from #11 worked: the PR was opened by the script.
- **Factory problem found:** two branches that both append to `decisions.md` conflict. A shared append-only log invites merge conflicts with agent branches.

| Date | Issue | Target | Basic A/B | Result | Questions asked | Where Adam stepped in | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-25 | #15 Runner execution (T2.2) | factory | A | Merged (PR #16) | 0 | Approved, started the run by hand, merged. Merge conflicts on `decisions.md` (3 times) fixed by Claude. | Good code. Review found that the allowlist is not a security boundary. |
| 2026-11-25 | #17 Result parsing (T2.3) | factory | A | Merged (PR #18) | 0 | Approved, started the run by hand, merged. | First run under the new rules: clean PR, decisions in the commit body. |
| 2026-11-25 | #20 Runner README | factory | **B** | PR #22 in Your QA | 0 | Approved only. The build, push and PR were automatic. | First fully automatic run. Delayed by n8n running old workflow versions. |

### #15 – Runner execution (T2.2)
- **Agent:** background thread, worktree reuse, process-group kill on timeout, a run never stays `running`, only the runner pushes. 11 unit tests with a fake agent.
- **Review (Claude):** 11/11 tests pass. A real `claude -p` smoke run against a sandbox clone (local bare repo as `origin`) was `done` in 15 s. `curl` was blocked by the allowlist, but `Bash(python3:*)` could still run any code, so the allowlist is only a guardrail (fixed in T2.3, the real boundary is T3.2).
- **Problem:** the PR conflicted with `main` three times, because the agent and Claude both appended to `decisions.md`/`PLAN.md`. This led to the rule that agents don't edit shared docs.

### #17 – Result parsing (T2.3)
- **Agent:** parses the last ```json block, and anything unclear becomes `stuck` without a push. Allowlist narrowed, env vars renamed. 18 tests.
- **New rules worked on the first try:** the PR touched only `runner/`, its decisions were in the commit body, and it merged cleanly.

### #20 – Runner README (first Basic B run)
- **Timeline:** Approved → WF2 v2 started run `ea86a86485ae` at 13:06 → `claude -p` wrote and committed the README (about a minute) → the runner parsed `done` and pushed → WF4 (activated later) opened PR #22 → `Your QA` at 13:16.
- **Factory problem found:** n8n had been running old versions of WF1 and WF2 since the day before (draft vs. published, swapped on import). The old WF2 posted the manual command twice before the cause was found with the MCP. The T1.4 race fix had never been live. Fixed by creating fresh workflows from the repo JSON.
- **Takeaway:** the automatic path works end to end. The weak spot was keeping n8n in sync with the repo, not the agent.
