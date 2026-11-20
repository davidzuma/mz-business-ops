---
name: lead-enrichment
description: Enrich qualified leads, verify contact data, and prepare CRM updates for approval.
---

# Lead Enrichment SOP

1. Read the lead list from `data/leads/`.
2. Verify each lead against approved public sources and the existing CRM.
3. Run `python3 scripts/sync_crm.py --input <file> --dry-run` to validate the proposed updates.
4. Present a change summary and identify uncertain fields.
5. Never write to the CRM or contact an external person until a human approves the changes.
