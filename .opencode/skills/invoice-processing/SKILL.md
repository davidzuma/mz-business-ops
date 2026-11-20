---
name: invoice-processing
description: Extract line items from vendor PDFs, categorize expenses, and append to the monthly ledger.
---

# Invoice Processing SOP

1. Locate new PDF files in `data/invoices/incoming/`.
2. Run `python3 scripts/parse_receipts.py --input <file>` to extract raw text and totals.
3. Map the vendor to the chart of accounts:
   - Cloud/Hosting -> `6100 - Infrastructure`
   - Software/SaaS -> `6200 - Subscriptions`
   - Contractors -> `6300 - Professional Services`
4. Append a validated row to `data/ledger_2026.csv` and move the processed PDF to `data/invoices/archived/`.
5. Output a summary table of processed items and flag any invoice over €500 for manual review.
