# Factory

A small software factory, built as an exam project. You write a task as a GitHub issue. n8n refines it with a local LLM, and after you approve it, Claude Code builds it on its own branch. Every result comes back as a pull request for review.

- Assignment: [Exam.project.description.md](Exam.project.description.md)
- Plan and task status: [PLAN.md](PLAN.md)
- Decisions: [documentation/decisions.md](documentation/decisions.md)

| Folder | Contents |
|---|---|
| `n8n/workflows/` | Exported n8n workflows (JSON) |
| `runner/` | Python runner that starts the coding agent |
| `prompts/`, `templates/` | AI step prompt, agent prompt, spec template |
| `projects/AdamAddon/` | Project the factory builds (git subtree) |
| `documentation/` | Decision log, evaluation log, report |
