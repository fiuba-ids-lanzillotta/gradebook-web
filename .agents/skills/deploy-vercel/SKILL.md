---
name: deploy-vercel
description: Checklist to deploy the frontend to Vercel (config and required environment variables)
allowed-tools:
  - read
  - grep
  - glob
permissions:
  allow:
    - Read(**)
---

Guide the deploy of `gradebook-web` to Vercel. Mostly a checklist; do not commit secrets.

## Config

- `vercel.json` defines a Python function over `app.py` with `includeFiles: "**"` — needed because
  a server-rendered frontend must bundle `templates/` and `static/` (unlike an API).
- `app.py` builds absolute paths (`BASE_DIR`) for `templates/`/`static/` so they resolve on Vercel.

## Environment variables (Vercel dashboard, NOT via .env)

- `SECRET_KEY` — long random value (`python -c "import secrets; print(secrets.token_hex(32))"`).
- `API_BASE_URL` — URL of the **deployed** `gradebook-api`
  (e.g. `https://<api>.vercel.app/gradebook_api`), not `localhost`.
- `API_KEY` — same value as `gradebook-api` (only if the API enforces it).
- `RECAPTCHA_SITE_KEY` — public site key rendered in the login widget. Not secret, but must be the
  site key paired with the `RECAPTCHA_SECRET` configured in `gradebook-api`.

## Notes

- The frontend has no database; it depends on `gradebook-api` being reachable at `API_BASE_URL`.
- The student zone (`site/`) and docente zone (`/admin`) both need the API to log in; the app
  only degrades gracefully on public reads, which this project barely uses.
