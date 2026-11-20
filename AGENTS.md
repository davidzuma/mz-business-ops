# Business Operations Agent Context

## Purpose

This repository contains modular workflows for the MZ business operations team.
Keep outputs factual, concise, and ready for human review.

## Repository layout

- `.opencode/skills/` contains reusable standard operating procedures.
- `.opencode/agents/` contains specialized sub-agents with restricted tools.
- `.opencode/commands/` contains one-shot slash commands.
- `scripts/` contains deterministic parsing, querying, and synchronization helpers.
- `templates/` contains reusable Markdown output formats.
- `data/` is a local drop-zone for inputs and generated outputs.

## Operating rules

- Never place credentials or other secrets in source files or prompts.
- Read environment values from environment variables or local `.env` files.
- Never send external email, message customers or partners, or modify production systems without explicit human confirmation.
- Never delete source or ledger data; archive or confirm it before movement.
- Use deterministic scripts for calculations, parsing, and CSV/database operations instead of manual computation.
- Flag estimates, inferred values, and anomalies for human review.
- Prefer minimum necessary access and do not use write or bash tools unless the task requires them.

