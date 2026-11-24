---
name: proposal
description: Create MZtech client proposals as branded 16:9 PDF decks (HTML -> headless Chrome) from a JSON content file, following the Ebro Fleet Control reference.
---

# Proposal SOP — follow every step in order. Do not skip steps. Do not improvise.

Goal: a PDF proposal deck for human review. Reference format:
`examples/Ebro Fleet Control Proposal.pdf`. Full schema documentation:
`templates/proposal/README.md` and `templates/proposal/example.json`.

Paths are relative to the repo root. Run commands from the repo root.

## Rules (never break these)

- NO MZtech logo image in the deck. The cover uses the typographic brand
  name only. NEVER set `meta.logo`.
- EVERY proposal MUST include project-specific designs: a "Diseño y demo"
  section with screenshots + live URL from the `poc` skill. If no PoC
  exists yet, run the `poc` skill FIRST (its STEP 8 tells you what to copy
  here). The builder flags decks without design slides.
- NEVER invent: prices, hours, SLAs, client legal names, company legal
  data, signatories, case-study figures, people, professors, testimonials,
  credentials or awards. Unknown value = leave the field empty ("") and let
  the builder flag it, or ask the user. Never present a fabricated person or
  quote as real: it can bias the client and is a misrepresentation.
- Money: `pricing.items[].amount` are NUMBERS in euros (sin IVA). The
  script sums them; never compute totals by hand. If the user gave a
  budget, the items must sum EXACTLY to it (pass `--budget` to check).
- Language: `meta.language` is `"es"` (default) or `"en"`; it translates
  every fixed deck label. Author the content fields in the same language as
  the client. If unsure, write in the client's language.
- Never email or share the PDF externally. `data/` is gitignored.

## STEP 1 — Collect inputs (ask the user for anything missing)

Required from the user or source documents:

1. Client name (short + legal if known), project name.
2. Budget (€) and duration (weeks/months). If given, they are constraints.
3. Scope: what is included, what is excluded, assumptions.
4. Demo: the PoC manifest `data/pocs/<slug>/poc.json` + screenshots
   (from the `poc` skill). If missing, run the `poc` skill first.
5. Company legal name, CIF/NIF, signatory. Known defaults (already in the
   builder): legal name `MZ Asesoría y Consultoría SL`, signatory
   `David Zumaquero Mairena`. Only the CIF/NIF is still unknown: if the
   user does not provide it, leave `meta.company.tax_id` as "" — the
   builder then shows the legal name alone in the signature block (no
   placeholder) and notes it in the flags. Never guess a tax ID.

Optional (skip the section if absent): functional detail, architecture,
security, team, maintenance, recurring costs, metrics, case studies.
For small projects keep only: cover, TOC, designs, scope+exclusions,
planning, pricing, costs, maintenance, legal.

## STEP 2 — Write the content JSON

```
mkdir -p data/proposals/<slug>
cp templates/proposal/example.json data/proposals/<slug>/proposal.json
```

Edit `data/proposals/<slug>/proposal.json`. Field rules:

- `meta.title`: "Client - Project" (or the project name if client unknown).
- `meta.language`: `"en"` or `"es"` — must match the client's language.
- `meta.payment_terms`: use the agreed wording verbatim (e.g. "50% at the
  end of week 2. Remaining 50% on delivery."). Never invent payment terms.
- `meta.company.brand`: "MZtech". Legal name and signatory have defaults;
  only the CIF/NIF must come from the user.
- Rich-text fields (`scope.intro`, `scope.items`, `*.items`, `caption`,
  `summary`, `rhythm`, `intro`, `includes`, `legal.items[].html`) accept
  inline HTML. Bold key terms with `<strong>`. Plain fields (names,
  concepts, durations) are escaped automatically — no HTML there.
- `demo.slides`: one entry per design screen. Set `image` to the PoC
  screenshot path, `url` to the live URL, `note` to the mockup disclaimer
  (see poc skill STEP 8). `heading` = screen name.
- `planning.gantt.bars`: `start`/`end` are week numbers within
  `gantt.weeks`; months' `span` values must sum to `weeks`.
- `pricing.items`: split the budget across phases; amounts must sum to
  the budget. Durations must match the planning.
- `costs.items`: third-party/recurring costs (hosting, DB, payment fees,
  domain). Use strings like "≈ 20 $ / mes" for estimates and say
  "orientativo" in the note. This slide matters for small projects.
- `maintenance`: hours bundle, €/h, what it covers, expiry rules.
- Delete any example section you do not use (e.g. `metrics`, `cases`,
  `assumptions`) — do not leave fictional example content in a real deck.

## STEP 3 — Build

```
python3 scripts/build_proposal.py --input data/proposals/<slug>/proposal.json --budget <BUDGET>
```

(Omit `--budget` only if the user gave no budget.)

Expected output: `HTML deck: ... (N slides)`, `PDF: ... (N pages)`,
`Pricing total (sin IVA): X€`, then `FLAGS FOR HUMAN REVIEW:` or `No flags.`

## STEP 4 — Verify (all checks must pass)

1. Slide count == page count in the output. If different, a slide
   overflowed: shorten its bullets or split it into two slides, rebuild.
2. Pricing total == budget (the script flags a mismatch; fix amounts).
3. Render and READ these pages with the read tool (checks stay inside the
   gitignored proposal folder):
   ```
   pdftoppm -png -r 80 -f 1 -l 3 data/proposals/<slug>/proposal.pdf data/proposals/<slug>/check
   ```
   Check: cover has NO logo image; TOC page numbers look right; the
   design slide shows the project screenshot. Also render the pricing
   page (find its number in the TOC) and check the total row.
4. Resolve or report every flag. `[PENDIENTE DE CONFIRMAR]` flags are
   expected when legal data is unknown — list them for the user; do not
   fill them with guesses.

## STEP 5 — Deliver for review

1. Show the PDF to the user:
   `tools.browser.preview({ path: "data/proposals/<slug>/proposal.pdf" })`
   (load the `browser` skill first if needed).
2. Summarize: total, duration, live demo URL, and the full flag list.
3. STOP. The user reviews and sends. Never send it yourself.

## Failure modes — what to do

| Symptom | Cause | Fix |
|---|---|---|
| `PDF not rendered` / Chrome not found | Chrome missing | Ask user to install Chrome or set `CHROME_PATH`. |
| Pages > slides | Slide overflow | Trim bullets / split slide; rebuild. |
| `Image not found, skipped` | Wrong screenshot path | Use the exact path from `poc.json`/screenshots dir; rerun poc STEP 6 if missing. |
| Budget mismatch flag | Amounts don't sum | Adjust `pricing.items` amounts; rebuild. |
| Gantt bar out of range | start/end > weeks | Fix week numbers; rebuild. |
| JSON decode error | Invalid JSON | Validate with `python3 -c "import json;json.load(open('<file>'))"`; fix commas/quotes. |

If something is not covered here, stop and ask the user.
