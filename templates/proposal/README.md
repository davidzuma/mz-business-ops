# MZtech proposal deck system

Branded 16:9 proposal decks, reproduced from the reference
`examples/Ebro Fleet Control Proposal.pdf` and rebranded for MZtech.

## How the reference proposal was created (reverse-engineered)

PDF metadata (`pdfinfo`) shows `Creator: HeadlessChrome/146`,
`Producer: Skia/PDF m146`, page size **1440 x 810 pt** (16:9), 20 pages.
So the original was an **HTML slide deck printed to PDF with headless
Chrome**, not a Word/InDesign document:

1. One fixed-size HTML section per slide (1920 x 1080 CSS px, which Chrome
   prints at 96 dpi as 1440 x 810 pt), `@page { margin: 0 }`.
2. Webfonts **Poppins** (headings) + **Be Vietnam Pro** (body), embedded as
   subsets in the PDF. Palette: ink `#00002e`, accent `#573cff`,
   muted `#596580`, pale-blue background.
3. Slide anatomy: cover with mesh-gradient background + logo + two-tone
   tagline; auto-numbered TOC with dotted leaders; section headers
   (accent number + title + horizontal rule); bullet slides with bold key
   terms; demo slides (browser-framed screenshot left, copy right);
   CSS-grid Gantt; pricing table with computed total; metrics cards;
   case-study slides (Sector/Solución/Duración + RETO/SOLUCIÓN/IMPACTO);
   legal bases + two-column acceptance/signature block.
4. Footer on every slide except the cover:
   `YYYY · Company` (left) and `Propuesta: <title> · N / total` (right).
5. Rendered with headless Chrome `--print-to-pdf` (no headers/footers).

## MZtech adaptation

- **No logo on the cover** (brand rule): the cover shows the typographic
  brand name + tagline. An image is only used if `meta.logo` is explicitly
  set — do not set it.
- **Project-specific designs are mandatory**: every proposal includes a
  "Diseño y demo" section built from the `poc` skill's screenshots + live
  URL. The builder flags decks without design slides.
- Palette sampled from `media/mztechlogo.jpg`: navy `#282769`,
  blue `#1a407e`, cyan `#178dc2`, sky `#16add8`; ink `#101038`,
  muted `#596580`, background `#eef3fa`.
- Cover gradient is pure CSS (radial gradients), no image asset needed.
- Logo: `media/mztechlogo.png` — transparent, whitespace-trimmed derivative
  of `media/mztechlogo.jpg` (the JPG's white background would print as a
  visible box; CSS blend modes do not survive Chrome's PDF export).
- Fonts are vendored in `fonts/` (latin woff2), so builds work offline.

## Files

- `deck.html` — CSS design system + `{{FONTS}}`/`{{SLIDES}}`/`{{TITLE}}` slots.
- `example.json` — full content model with a fictional worked example
  (Nordia - Dock Scheduler). Every key is optional except `meta`; absent
  sections are skipped and numbering/TOC adapt automatically.
- `fonts/` — Poppins 500/600, Be Vietnam Pro 400/500/600 + `fonts.css`.

## Content model (summary)

```
meta: language ("es" default | "en"), client_short, client_legal, project,
      title?, year, tagline[2],
      logo?, company{brand, legal_name, tax_id, signatory},
      validity_days, payment_terms, overrun_clause
demo.slides[]: title, heading?, note?, caption(html), image?, url?, url_label?
scope: intro[html], items[html], exclusions[html]
functional[] / architecture[] / security[]: {heading, items[html], note?}
assumptions[]: {id, html}
planning: summary(html), phases[{label, html}],
          gantt{weeks, months[{label, span}], bars[{label, start, end, color}]}
team: rows[{role, scope}], rhythm(html), collab[html]
pricing.items[]: {phase, concept, detail?, duration, amount(number)}  -> total computed
costs: intro?(html), items[{concept, kind, amount(number|string), note?}], note?(html)
       (recurring/third-party costs slide; kind: Único|Mensual|Anual|Por transacción)
maintenance: intro(html), includes[html], items[{concept, hours, amount}]
metrics[]: {big(html), caption(html)}          (3 cards)
cases[]: {name, sector, solution, duration, challenge, solution_detail,
          impact, image?, logo?}
legal: items[{title, html}], acceptance?(html)
```

Rich-text fields pass inline HTML through (`<strong>`, `<a>`, `→`, `<br>`);
plain fields are escaped. Gantt colors: `navy | blue | cyan | sky | slate`.
Amounts are numbers (EUR, sin IVA); the script formats them es-ES
(`14.580€`) and sums the total.

## Build

```
python3 scripts/build_proposal.py --input <proposal.json> [--budget <EUR>] [--outdir DIR] [--no-pdf]
```

`--budget` flags any mismatch between the pricing total and the agreed
budget. The builder also flags decks without design/demo slides.

Requires Google Chrome or Chromium (override with `CHROME_PATH`).
The script copies fonts and images into the output dir, writes
`proposal.html`, renders `proposal.pdf`, verifies page count vs slide
count (overflow detection) and prints flags for human review
(missing company data, unresolved placeholders, missing images,
out-of-range Gantt bars).
