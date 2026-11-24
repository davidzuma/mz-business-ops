# mz-business-ops-

Repository structure for OpenCode-driven business automation.

OpenCode loads `AGENTS.md` globally, modular SOPs from `.opencode/skills/`,
restricted sub-agents from `.opencode/agents/`, and slash commands from
`.opencode/commands/`. Deterministic helpers live in `scripts/`, reusable
outputs in `templates/`, and local working files in `data/`.

## Included workflows

- `/invoice` processes incoming vendor PDFs.
- `/report` generates the weekly operations report.
- `/proposal` drafts branded client proposal decks (PDF) for human review.
- `/poc` builds mock-data prototypes deployed to Vercel for proposal demos.

## Safety

State-changing actions require human confirmation. Never commit secrets or
business data in `data/`; the repository `.gitignore` excludes local data,
environment files, and common client/customer export folders.
