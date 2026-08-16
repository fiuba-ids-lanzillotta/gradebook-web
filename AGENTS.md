# AGENTS.md

Guide for agents (and people) working on **gradebook-web**. Keep it short and actionable.

## Overview

Server-rendered **base** frontend (**Flask + Jinja2**) that consumes the backend API
**`gradebook-api`** over HTTP. Renders public pages and an admin panel, and manages the example
resource **`items`** (`{id, nombre, descripcion, activo}`) through the API. It has **no database**
of its own. Meant as a starting point for a real frontend; follows the same style/architecture as
the rest of the workspace (based on `ids-web`).

## How to run

```bash
setup_virtualenv.bat        # Windows
./setup_virtualenv.sh       # Linux / macOS

# or manually
python -m venv .venv && .venv\Scripts\activate   # (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
python app.py               # http://localhost:5001
```

Needs a `.env` (see `.env.example`). The admin panel requires `gradebook-api` running to log in;
the public pages degrade gracefully if the API is down.

## Environment (`.env`)

- `SECRET_KEY` — Flask session signing (random, gradebook-web only).
- `API_BASE_URL` — base URL of `gradebook-api` (default `http://localhost:5000/gradebook_api`).
- `API_KEY` — **shared** with `gradebook-api`; sent as the `X-API-Key` header. Empty if the API is public.

## Verification (run before considering a change done)

```bash
pip install -r requirements-dev.txt
pytest                        # tests de services y rutas (requests mockeado, sin red)
python -m compileall -q web app.py
python -c "import jinja2, pathlib; env=jinja2.Environment(); [env.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('templates').rglob('*.html')]; print('templates OK')"
```

Los tests cubren las funciones puras, los services y las rutas (`test_client`) con `requests`
mockeado (`conftest.py` da las fixtures `respuesta_falsa` y `cargar_json`, y fija env dummy). No
requieren `gradebook-api` corriendo. Las respuestas de la API se guardan como **mocks JSON** en
`tests/resources/json/<dominio>/` y se cargan con `cargar_json` (patrón `<dominio>/<nombre>.json`).

## Code conventions

- **Functional style, no classes.** Data passed to templates as `dict`/`list`.
- **Avoid `break`/`continue`/`pass`** unless strictly necessary or unavoidable (e.g. `pass` in an
  `except`); prefer clear `if`/`else`.
- **Spanish naming, no abbreviations** (self-explanatory variables).
- **Layers**: `routes` (Flask blueprints, presentation/flow) → `services` (HTTP calls to
  `gradebook-api` via `requests`). Routes hold no HTTP-client logic; services encapsulate the API calls.
- **Blueprints**: `web` → `site` (public pages, no prefix) + `admin` (`/admin`). Templates mirror
  this: `templates/site/` and `templates/admin/`.
- **All calls to `gradebook-api`** go through `web/services/*.py` and MUST include the API key via
  `api_headers()` (`web/constants.py`). **Public reads degrade gracefully**: on any non-200,
  return empty (`[]`) so the page still renders.
- **Admin auth**: `POST /login` on the API returns a JWT stored in `session['token']`; admin routes
  use `@admin_required` and send `Authorization: Bearer <token>`. On 401/403 from the API, the
  services return `{'unauthorized': True}` and the route clears the session and redirects to login.

## How to add a new section/resource

Mirror the `items` pattern:
1. `web/services/<recurso>.py`: HTTP calls to the API (reads degrade gracefully; writes return
   `{'ok': ...}` and use `respuesta_no_autorizada` / `mensaje_error_api` from `respuestas_api.py`).
2. `web/routes/site/<recurso>.py` and/or `web/routes/admin/<recurso>.py`: thin blueprints; register
   them in the corresponding `__init__.py`.
3. `templates/site/<recurso>.html` / `templates/admin/<recurso>.html` extending `base.html`.
4. Tests: services (with `requests` mockeado) + a route test (`app.test_client()`), plus JSON mocks
   under `tests/resources/json/<recurso>/`.

## Gotchas

- `API_KEY` must match `gradebook-api`'s (shared secret). Rotate it in both at once.
- `app.py` uses absolute paths (`BASE_DIR`) for `templates/` and `static/` so Vercel finds them.
- Vercel bundles everything (`includeFiles: "**"`) because it needs `templates/` and `static/`.
- The web runs on port **5001**; the API on **5000** — so both can run locally at the same time.

## Deploy

Vercel (`vercel.json` → Python function over `app.py`, `includeFiles: "**"`). Set env vars in the
dashboard: `SECRET_KEY`, `API_BASE_URL` (the deployed API, not localhost), `API_KEY` (same as
`gradebook-api`).

## Git

- Commit messages in Spanish, focused on the "why".
- Do not push unless explicitly asked. The team merges to `main` via Pull Requests.

## Pointers

- Backend it consumes: `../gradebook-api` (see its `AGENTS.md`, `README.md` and `docs/swagger.yaml`).
