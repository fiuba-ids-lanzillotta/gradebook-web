---
name: sync-docs
description: Audit and update README.md so the documentation matches the current frontend code
allowed-tools:
  - read
  - edit
  - grep
  - glob
permissions:
  allow:
    - Read(**)
  ask:
    - Write(README.md)
---

Keep `README.md` in sync with the code. **Only touch documentation** — never change app code here.
(`gradebook-web` has no OpenAPI spec; the API contract is documented in
`../gradebook-api/docs/swagger.yaml`.)

## Sources of truth

- `app.py` and `web/routes/**` — registered blueprints, pages and URL prefixes (`site` = zona
  alumno sin prefix, `/admin` = backoffice docente).
- `web/routes/admin/panel.py` — `SOLAPAS`/`SOLAPA_PERMISO`: las secciones reales del sidebar.
- `web/constants.py` — env vars read (`API_BASE_URL`, `API_KEY`, `RECAPTCHA_SITE_KEY`),
  `MATERIA_CODIGO`, fallbacks `CURSADA_*` y códigos `PERMISO_*`.
- `web/auth_sesion.py` — split de zonas (`login_required` alumno vs `admin_required` docente).
- `web/services/**` — which data comes from `gradebook-api`.
- `.env.example` — the full set of environment variables.
- `vercel.json` — deploy config.

## What to check and fix in `README.md`

- **Environment variables** table lists exactly what the app reads (`SECRET_KEY`, `API_BASE_URL`,
  `API_KEY`, `RECAPTCHA_SITE_KEY`) with defaults, matching `.env.example`.
- **Project structure** tree reflects the real files/dirs (`web/routes/site`, `web/routes/admin`,
  `web/services`, `templates/site`, `templates/admin`, `tests/resources/json`, `.agents/`, etc.).
- **Pages/routes** description matches the actual blueprints and pages (incluyendo qué solapas
  del admin están activas vs placeholder).
- **Setup / deploy** steps match the scripts (`scripts/setup_virtualenv.*`) and `vercel.json`.
- No stale references (removed pages, the `items` example resource if it gets dropped, old env vars).

## Deliverable

Report the mismatches found and the fixes applied. If everything was already consistent, say so.
