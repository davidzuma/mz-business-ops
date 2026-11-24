# MZtech PoC scaffold

Vite + React + TypeScript prototype with mock data, branded with the MZtech
UI kit (`src/styles.css`). Used by the `poc` skill; deployed to Vercel and
attached to proposals as the interactive demo.

## Rules

- **Mock data only** — fictional names, plates, numbers. Never real client
  data or credentials. No backend, no auth, no analytics.
- Keep the "Demo · datos ficticios" badge visible on every screen.
- Data layer: `src/data/fixtures.ts` (typed fixtures, dates relative to
  today) + `src/lib/mock.ts` (fake latency, localStorage persistence,
  overlap/date helpers). Keep the async shape so a real API can replace it.
- Implement the core flow end-to-end (create → approve → use → close, or
  the project's equivalent) so the prototype is genuinely usable.
- Associate every form label with its control (`htmlFor`/`id`) for
  accessibility and testability.
- Make views deep-linkable via `location.hash` (see shell) so proposals
  can link directly to a specific screen.

## Commands

```
npm install
npm run dev       # local dev server
npm run build     # type-check + production build (must pass before deploy)
npm run preview   # serve the production build locally
```

Deploy via `scripts/deploy_poc.py` from the ops repo (GitHub repo + Vercel
production deployment + `poc.json` manifest).
