---
name: profile-deck
description: Create concise, anonymized MZtech client decks from multiple CVs, role briefs, portraits, certification badges, and user-provided rates.
---

# MZtech Profile Deck SOP

Create a direct, English-language PDF to present professional profiles to a potential client. Use the MZtech proposal deck's 16:9 visual system, but do not include proposal sections such as pricing tables, scope, or a table of contents.

## 1. Collect and check inputs

Required:

1. Role/profile brief, for relevance and terminology only.
2. One CV or verified profile per person.
3. One usable portrait per person. Prefer a separate user-provided portrait; extract the embedded portrait from the CV if that is the supplied source. If an inline attachment is not accessible as a local file, ask for the image file/path. Never substitute a generated or different person's portrait.
4. Order of presentation, if specified.

Optional; include only when the user supplies them:

- Daily rates (currency and unit; default presentation is `€N / day` only when the user gave a EUR daily rate).
- Public LinkedIn/profile URLs for additional experience details.
- Requested credentials, logos, slogan, or client-specific terminology.

Use `media/mztechlogo.png` and the current mztech.dev slogan, **“Simple, reliable technology”**, unless instructed otherwise.

## 2. Source and curate the profile facts

- Read PDFs with `pdftotext -layout`; use `pdfimages -all` to extract embedded portraits/certification marks when helpful. Read DOCX text from the document or its XML if a DOCX parser is unavailable.
- For LinkedIn, use only publicly available pages/search results; do not sign in or bypass access controls. If LinkedIn blocks direct access, use the supplied CV and public indexed snippets only, then note that limitation to the user.
- Keep a `sources.md` in the job folder mapping experience, education, certification names, and dates used in the deck back to each CV/profile source.
- Summarize in client-ready English. Use exact, verified dates and company names. Group experience by employer with company, position, date range, and concise bullets.
- Keep job titles accurate. If the user requests a client-facing title different from the source title, preserve the source title in parentheses or ask before changing it.
- Treat role requirements as context, not proof. Never upgrade skills, years, seniority, outcomes, or certifications to make a profile appear to fit.
- Include all certifications selected for the profile deck. Pair every certification with its actual badge/logo where available. Prefer badges in the CV or assets supplied by the user; otherwise use an official issuer/certification source and keep the downloaded image local. If no suitable logo or the issuer is unclear, use the builder's neutral credential emblem with the verified credential label; never assign an unverified issuer.
- Include relevant degrees/programs under Education. Do not present a course certificate as a degree.
- Do not include candidate names, email addresses, phone numbers, LinkedIn URLs, or other personal contact details in the deck unless explicitly requested. Employer names are fine.
- Use a supplied rate exactly. Never infer or calculate one. Do not add VAT/tax claims unless specified.

## 3. Prepare the job folder and JSON

Use `data/profile-deck/<slug>/` (gitignored) for each deck:

```text
data/profile-deck/<slug>/
  profiles.json
  sources.md
  assets/
    profile-01.jpg
    certification-badge.png
```

Start from `templates/profile-deck/profiles.example.json`. Profile fields:

- `role`, `positioning`, `summary`
- `photo`: local asset path relative to `profiles.json`
- `experience[]`: `{company, title, period, highlights[]}`
- `education[]`: `{degree, school, period}`
- `skills[]`: role-relevant toolkit
- `certifications[]`: verified credential labels; if there is no logo, the builder uses a neutral emblem
- `certification_badges[]`: `{image, label, wide?}`; one entry per certification when using sourced logos/badges
- `daily_rate`: optional user-provided number

Keep the requested candidate order. Use one profile object per candidate. Do not put personal names in `role`, `positioning`, or slide text.

## 4. Build

From the repository root:

```sh
python3 scripts/build_profile_deck.py \
  --input data/profile-deck/<slug>/profiles.json
```

The builder writes `profile-deck.html` and `profile-deck.pdf` into the same folder. It uses Chrome/Chromium; set `CHROME_PATH` if browser discovery fails.

## 5. Verify before delivery

1. Confirm the PDF contains exactly one cover plus one slide per profile:

   ```sh
   pdfinfo data/profile-deck/<slug>/profile-deck.pdf | grep Pages
   ```

2. Render and inspect every slide:

   ```sh
   pdftoppm -png -r 80 data/profile-deck/<slug>/profile-deck.pdf \
     data/profile-deck/<slug>/review
   ```

3. Check that:
   - each portrait is the correct person and not cropped awkwardly;
   - the cover logo, slogan, and light palette match the profile slides;
   - left-column summary/toolkit/certifications and right-column experience/education are legible;
   - employer, title, dates, order, and supplied daily rates are correct;
   - every certification shown has a badge/logo or the neutral emblem;
   - no names or contact details leaked into PDF text;
   - the PDF has no overflow, clipping, missing images, or blank experience cards.

4. Open the final PDF in the Review pane with `tools.browser.preview`.
5. Deliver the file path, summarize the order/rates if provided, and flag any unresolved source or role-fit caveat. Never send the deck externally.

## Design system

- 1920 × 1080 CSS pixels, 16:9, printed PDF.
- Proposal-inspired MZtech colors: navy `#282769`, blue `#1a407e`, cyan `#178dc2`, sky `#16add8`, pale blue `#eef3fa`.
- Poppins headings and Be Vietnam Pro body fonts from `templates/proposal/fonts/`.
- Cover uses the MZtech logo and slogan on the same pale palette as profile slides.
- Profile layout: smaller portrait, summary, technical toolkit, and certification badges/logos on the left; title, daily rate when supplied, company-grouped experience, and education on the right.
- Keep slides concise and factual; do not add names or personal contact details.
