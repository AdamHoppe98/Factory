# Refine step – example (T1.2)

Run outside n8n with `scripts/try-refine.py`: qwen3:8b, `think: true`, temperature 0.2, prompt `prompts/refine.md` with `templates/spec-template.md` filled in. Date: 2026-11-24.

## Input (issue #101, sample)

```
Title: Show durability in the addon

**What:** a page that shows my gear durability, warn me when something is low

**Target:** projects/AdamAddon
```

## Output (43 s)

```markdown
<!-- factory:spec -->
## Spec for #101

**Target:** projects/AdamAddon

### Goal
Add a durability tracking feature that displays gear durability and shows warnings when it falls below a threshold.

### Why
To help track gear maintenance needs and prevent gear breakage by providing visual feedback and alerts.

### Scope
- In: 
  - Create a new feature file for durability tracking
  - Add a dedicated page in the UI for durability display
  - Implement warning system for low durability
  - Store durability data in character database
- Out: 
  - No changes to existing features
  - No integration with external APIs

### Constraints
- Only change files inside the Target.
- Use existing UI framework and database systems

### Acceptance criteria
- [ ] Durability page displays current gear durability values
- [ ] Warning indicator appears when durability < 30% (configurable)
- [ ] Durability data persists between sessions in character DB

### How to test
1. Reload UI with `/reload`
2. Navigate to durability page via `/adam durability`
3. Verify durability values are displayed
4. Check warning indicator when durability < 30%
5. Log out and back in to confirm data persistence

### Open questions
1. What threshold percentage should trigger the warning? (Default: 30%)
2. Should durability values be displayed as text or progress bars?
3. How should the warning indicator be implemented (tooltip, color change, etc.)?
```

## What the test runs showed

Three sample ideas: an addon feature (#101), a runner endpoint (#102) and a vague idea with no target (#103).

| Version | Template followed | Rule breaks |
|---|---|---|
| v1, no thinking (10–28 s) | 3/3 | #102 made up port 8080. #103 picked a target without asking and assumed a config system. |
| v2, facts added to the prompt, no thinking (10–17 s) | 3/3 | #102 fixed. #103 still didn't ask about the target. #101 dropped its questions. |
| v2, thinking (43–56 s) | 2/2 | #103 asked about the target. Both still add a few unasked details (persistence, "existing UI framework"). |

Thinking mode is used in n8n. Adam's review in `Ready for approval` is still needed to catch invented details.
