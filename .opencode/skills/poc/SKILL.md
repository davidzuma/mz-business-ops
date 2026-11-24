---
name: poc
description: Build a working mock-data prototype (PoC) from a description, deploy it to Vercel with a private GitHub repo, and hand the live URL + screenshots to the proposal skill.
---

# PoC SOP — follow every step in order. Do not skip steps. Do not improvise.

Goal: a deployed, clickable prototype with fictional data that proves the
core flow of the project. Its URL and screenshots go into the proposal.

Paths below are relative to the repo root
(`/Users/davidzumaquero/GitHub/mztech/mz-business-ops`). Run all commands
from the repo root unless a step says otherwise.

## Rules (never break these)

- ONLY fictional data: invented names, emails, plates, card numbers,
  prices. NEVER real client data, credentials, API keys or tokens.
- NEVER invent a person, professor, doctor, testimonial, award, credential,
  client logo or success metric. A made-up expert profile or quote can bias
  the client and read as a real endorsement. For those blocks use a neutral
  placeholder that describes the slot ("Meet the professor — profile
  provided by the client", "Testimonial slot · real quote pending") and keep
  the final layout. Real-looking numbers must come from the project data
  (counts of courses, lessons, etc.), never from invented traction.
- No backend, no real auth, no real payments, no analytics scripts.
- Keep a visible demo badge on every screen, in the project language:
  "Demo · datos ficticios" (ES) or "Demo · fictional data" (EN).
- The visual design must fit the PROJECT (an academy looks academic, a
  logistics tool looks operational). `templates/poc/src/styles.css` is a
  starting point: override colors, fonts and layout for the project.
- The GitHub repo is PRIVATE unless the user explicitly says public.
- Never send the URL to customers/partners. Show it to the user only.

## STEP 0 — Check tools and login (STOP if missing)

Run these two commands:

```
vercel whoami
gh auth status --active
```

- `vercel whoami` must print a username. If it prints an error, STOP and
  ask the user: "Please run `vercel login` and tell me when done."
- `gh auth status --active` must show `✓ Logged in`. If not, STOP and ask
  the user: "Please run `gh auth login` and tell me when done."
- Do NOT attempt to log in yourself. Do NOT continue until both pass.

## STEP 1 — Name the project and confirm with the user

1. Derive `<slug>`: lowercase, words joined by hyphens, only a-z0-9-
   (example: `online-academy`).
2. The deploy name is `mztech-demo-<slug>`.
3. Ask the user ONE question to confirm: project name, slug, and that the
   repo will be private. Wait for the answer before continuing.

## STEP 2 — Copy the scaffold

```
cp -R templates/poc data/pocs/<slug>
```

Then edit ONLY these files inside `data/pocs/<slug>/`:

| File | What to do |
|---|---|
| `index.html` | Set `<title>` to the project name. |
| `src/data/fixtures.ts` | Replace with the project's entities and fictional records. Use `dayISO(n)` for dates so the demo always shows activity. |
| `src/App.tsx` | Replace the shell with the project's screens and the core flow. |
| `src/styles.css` | Adapt the theme to the project (colors, fonts, layout). Keep the badge, responsive rules and component classes you reuse. |

Do not edit `package.json`, `vite.config.ts`, `tsconfig.json`,
`vercel.json` unless the build fails because of them.

## STEP 3 — Implement the prototype (checklist)

All boxes must be true before STEP 4:

- [ ] 2–4 screens reachable from a nav (sidebar or top nav).
- [ ] The ONE core flow works end-to-end with visible feedback
      (examples: request→approve→close; browse→enroll→pay→access).
- [ ] Forms validate input and show error messages (e.g. block overlaps,
      invalid card format). Use `htmlFor`/`id` on every label+control.
- [ ] State persists with `loadStore`/`saveStore` from `src/lib/mock.ts`;
      a "Reset demo" button restores fixtures.
- [ ] Views are deep-linkable with `location.hash` (see scaffold App.tsx).
- [ ] Demo badge visible ("Demo · datos ficticios" / "Demo · fictional data");
      footer says no backend.
- [ ] Loading states use `delay()`; empty states have a message.

## STEP 4 — Build (must exit 0)

```
cd data/pocs/<slug> && npm install --no-audit --no-fund && npm run build
```

- If TypeScript or Vite reports errors: fix them and rerun until the last
  line is `✓ built in ...`. NEVER continue with a failing build.
- Return to the repo root afterwards.

## STEP 5 — Verify locally in the browser

1. Start the preview server in the background:
   `cd data/pocs/<slug> && npm run preview -- --port 4173 --strictPort`
2. Load the `browser` skill, then open `http://localhost:4173` with
   `tools.browser.tabs.open`, wait for load, and read
   `tools.browser.console` at level `error`. The error list MUST be empty.
3. Click through the core flow with snapshot/click (or `evaluate` with
   `el.click()` when the accessibility snapshot truncates long pages).
   Confirm each action shows its toast/state change.
4. If anything fails: fix the code, rebuild (STEP 4), re-verify. The
   preview server serves `dist/`, so a rebuild is enough (no restart).

## STEP 6 — Screenshots for the proposal (desktop width)

The browser Review pane is narrow; use headless Chrome instead. From
`data/pocs/<slug>/` run one command per screen (create `screenshots/`
first with `mkdir -p screenshots`):

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --window-size=1600,1000 --virtual-time-budget=8000 --screenshot=screenshots/<name>.png "http://localhost:4173/<hash>"
```

- Required: the main screen (`/`) plus the 1–2 screens of the core flow
  (use their hashes, e.g. `/#aprobaciones`).
- If that Chrome path does not exist on this machine, ask the user for
  the Chrome/Chromium executable path; do not guess.
- Verify each PNG exists and is larger than 10 KB (`ls -la screenshots`).
  If a file is tiny or missing, rerun that command.
- Read the PNGs with the read tool to confirm they look correct.

## STEP 7 — Deploy (GitHub + Vercel)

From the repo root:

```
python3 scripts/deploy_poc.py --dir data/pocs/<slug>
```

Expected output lines: `GitHub: https://github.com/... (private)` and
`Live demo: https://mztech-demo-<slug>.vercel.app`. The script builds,
commits, creates the private repo, links Vercel, deploys to production
and checks HTTP 200.

- If it prints `ERROR: ... not logged in`: go back to STEP 0.
- If it prints `WARNING: ... did not return HTTP 200`: wait 30 s and open
  the URL with headless Chrome (STEP 6 command without --screenshot is
  not needed; use `curl -s -o /dev/null -w "%{http_code}" <url>`). If
  still not 200, tell the user and stop.
- Read `data/pocs/<slug>/poc.json` — it is the manifest for STEP 8.

## STEP 8 — Hand off to the proposal skill

Report to the user: live URL, repo URL, and the screenshot paths.
When building the proposal (see `proposal` skill), set in its JSON:

```
demo.slides[0].image = "data/pocs/<slug>/screenshots/<main>.png"
demo.slides[0].url   = <production_url from poc.json>
demo.slides[1].image = "data/pocs/<slug>/screenshots/<flow>.png"
demo.slides[1].url   = <production_url> + "/#<hash>"
```

Keep the mockup disclaimer in `demo.slides[].note`, in the deck language:
- ES: "Mockup de referencia: no constituye especificación funcional ni
  diseño cerrado. Datos ficticios, sin backend ni gestión de usuarios real."
- EN: "Reference mockup: not a functional specification or a closed design.
  Fictional data, no backend or real user management."

## If something is not covered here

Stop and ask the user. Do not guess commands, names or credentials.
