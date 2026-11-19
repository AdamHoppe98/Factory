#!/usr/bin/env bash
# Creates (or updates) the factory state labels on a GitHub repo.
# Colors follow the assignment diagram: orange = Adam acts, purple = AI works, pink = n8n moves the task.
# Usage: scripts/setup-labels.sh [owner/repo]   (default: AdamHoppe98/Factory)
set -euo pipefail

REPO="${1:-AdamHoppe98/Factory}"

label() { gh label create "$1" --repo "$REPO" --color "$2" --description "$3" --force; }

label "Ideas"              "f9e8cc" "Adam wrote a rough task"
label "Refining"           "e6dcf8" "AI step rewrites the task into a spec"
label "Ready for approval" "f9e8cc" "Adam reads the AI's spec"
label "Approved"           "f8e0e6" "Only Adam sets this; waits for the factory"
label "Building"           "e6dcf8" "Coding agent works on branch issue-N"
label "Waiting for you"    "f9e8cc" "Agent asked a question; Adam answers in a comment"
label "Stuck"              "f9e8cc" "Agent failed or ran over 30 min; retry or drop"
label "Your QA"            "f9e8cc" "Pull request is open; Adam reviews"
label "Done"               "f8e0e6" "PR merged or issue closed"
