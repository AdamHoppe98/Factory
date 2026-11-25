#!/usr/bin/env bash
# Basic A: run the coding agent by hand for one issue.
#
# Usage: scripts/run-manual.sh <issue> [--dry-run]
#
# Builds the prompt from prompts/agent.md, the latest factory:spec comment and
# the comments after it, then starts Claude Code (Sonnet) in a git worktree on
# branch issue-N. Afterwards it offers to push the branch and open the PR.
# --dry-run only prints the prompt.
set -euo pipefail

N="${1:?usage: scripts/run-manual.sh <issue> [--dry-run]}"
DRY_RUN="${2:-}"
ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
BRANCH="issue-$N"
WORKTREE="$ROOT/runner/worktrees/$BRANCH"
PROMPT_FILE="$ROOT/runner/logs/$BRANCH-prompt.md"
# Factory has two remotes (origin, adamaddon), so gh needs the repo named.
REPO="AdamHoppe98/Factory"

ISSUE_JSON="$(gh issue view "$N" --repo "$REPO" --json title,state,labels,comments)"

PROMPT="$(ISSUE_JSON="$ISSUE_JSON" N="$N" TEMPLATE="$ROOT/prompts/agent.md" python3 - <<'EOF'
import json, os, sys

issue = json.loads(os.environ["ISSUE_JSON"])
comments = issue["comments"]
spec_idx = [i for i, c in enumerate(comments) if c["body"].lstrip().startswith("<!-- factory:spec -->")]
if not spec_idx:
    sys.exit(f"Issue #{os.environ['N']} has no factory:spec comment. Refine it first.")

spec = comments[spec_idx[-1]]["body"].split("\n", 1)[1].strip()

# Q&A after the spec: the agent's questions and Adam's answers. Status comments are left out.
qa = []
for c in comments[spec_idx[-1] + 1:]:
    body = c["body"].lstrip()
    if body.startswith("<!-- factory:question -->"):
        qa.append("Agent asked:\n" + body.split("\n", 1)[1].strip())
    elif not body.startswith("<!-- factory:") and c["author"]["login"] == "AdamHoppe98":
        qa.append("Adam:\n" + body.strip())

text = open(os.environ["TEMPLATE"]).read()
for key, value in {"ISSUE": os.environ["N"], "TITLE": issue["title"],
                   "SPEC": spec, "QA": "\n\n".join(qa) or "None"}.items():
    text = text.replace("{{" + key + "}}", value)
print(text)
EOF
)"

# Manual run only: the push and PR happen in this script after Claude Code exits.
PROMPT="$PROMPT"$'\n\n'"This is a manual run. Adam watches the chat. Right before the JSON block, tell him: \"Type /exit. The script then pushes issue-$N and opens the PR.\""

mkdir -p "$(dirname "$PROMPT_FILE")"
printf '%s\n' "$PROMPT" > "$PROMPT_FILE"

if [ "$DRY_RUN" = "--dry-run" ]; then
  printf '%s\n' "$PROMPT"
  exit 0
fi

LABELS="$(jq -r '[.labels[].name] | join(", ")' <<<"$ISSUE_JSON")"
if [[ ", $LABELS, " != *", Building, "* ]]; then
  echo "Issue #$N is not Building (labels: ${LABELS:-none}). WF2 sets Building when it is the issue's turn." >&2
  exit 1
fi

# Worktree on issue-N: reuse it, continue the pushed branch, or start from main.
git -C "$ROOT" fetch -q origin
if [ -d "$WORKTREE" ]; then
  echo "Reusing worktree $WORKTREE"
elif git -C "$ROOT" show-ref -q --verify "refs/heads/$BRANCH"; then
  git -C "$ROOT" worktree add -q "$WORKTREE" "$BRANCH"
elif git -C "$ROOT" show-ref -q --verify "refs/remotes/origin/$BRANCH"; then
  git -C "$ROOT" worktree add -q -b "$BRANCH" "$WORKTREE" "origin/$BRANCH"
else
  git -C "$ROOT" worktree add -q -b "$BRANCH" "$WORKTREE" origin/main
fi

echo "Starting Claude Code on $BRANCH. Prompt saved to $PROMPT_FILE"
(cd "$WORKTREE" && claude --model sonnet "$PROMPT")

echo
echo "Commits on $BRANCH that are not on main:"
git --no-pager -C "$WORKTREE" log --oneline origin/main..HEAD
read -r -p "Push $BRANCH and open or update the PR? [y/N] " ANSWER
if [ "$ANSWER" = "y" ]; then
  git -C "$WORKTREE" push -q -u origin "$BRANCH"
  if [ -z "$(gh pr list --repo "$REPO" --head "$BRANCH" --state open --json number --jq '.[].number')" ]; then
    TITLE="$(jq -r .title <<<"$ISSUE_JSON")"
    COMMITS="$(git -C "$WORKTREE" log --format='- %s' origin/main..HEAD)"
    (cd "$WORKTREE" && gh pr create --repo "$REPO" --head "$BRANCH" --title "$TITLE" \
      --body "Closes #$N"$'\n\n'"Built by the factory (Basic A, manual run)."$'\n\n'"$COMMITS")
  else
    echo "PR already open. WF3 moves the issue to Your QA."
  fi
fi
