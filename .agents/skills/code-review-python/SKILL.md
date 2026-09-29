---
name: code-review-python
description: Iterative code quality improvement (naming, structure, clarity) for this Flask/Jinja frontend — routes/services and/or templates
argument-hint: "[scope: 'web', 'templates', 'both', or a specific path/pattern]"
allowed-tools:
  - read
  - edit
  - grep
  - glob
  - exec
permissions:
  allow:
    - Read(web/**)
    - Read(templates/**)
    - Read(AGENTS.md)
    - Exec(python -m compileall*)
    - Exec(python*)
    - Exec(pytest*)
  ask:
    - Write(web/**)
    - Write(templates/**)
---

Act as a **Senior Software Engineer and Code Reviewer**.

Progressively improve code quality in the specified scope without breaking existing functionality
or assuming changes outside the current scope.

## Scope

Review and improve: **$ARGUMENTS**

Valid scopes:
- `web` — Python (routes + services)
- `templates` — Jinja templates
- `both`
- A specific directory or file (e.g., `web/services/`)

If no scope is given, ask. When `both`, review Python first, then templates, keeping changes coordinated.

## Project conventions

Read `AGENTS.md` at the project root first and follow it.

## Main objectives

- Improve readability, maintainability and clarity.
- Clear, descriptive **Spanish** names, no unnecessary abbreviations.
- Preserve current behavior.

## Important rules

- **Do NOT introduce classes** (this project is intentionally functional).
- **Avoid `break`/`continue`/`pass`** unless strictly necessary or unavoidable (e.g. `pass` in an
  `except`); prefer clear `if`/`else`.
- Don't over-engineer.

## Production review criteria (`web/`)

- Naming in Spanish, descriptive, no abbreviations (`respuesta` not `r`, `error` not `e`).
- Layering respected: `routes` → `services`. Routes hold presentation/flow; the HTTP calls to
  `gradebook-api` live in `services` and go through `api_headers()` (never inline the `X-API-Key`).
- **Public reads degrade gracefully**: any non-200 from the API returns empty/fallback, never a crash.
- Permission gating consistent: admin routes check `tiene_permiso(PERMISO_*)` and use
  `redirigir_sin_permiso()` / `redirigir_a_login_sin_sesion()` on `{'unauthorized': True}` results;
  services use `respuesta_no_autorizada` / `mensaje_error_api` from `respuestas_api.py`.
- Imports grouped (stdlib / third-party / local); no wildcard/unused imports.
- No secrets in code; `SECRET_KEY`/`API_KEY`/`RECAPTCHA_SITE_KEY` only from env.

## Template review criteria (`templates/`)

- Reuse `base.html` (site + auth pages) and `admin/base_admin.html` (docente panel); keep
  `site/` and `admin/` separation.
- No business logic in templates; guard optional data (e.g. `{% if ... %}`) so missing/empty API
  data renders cleanly. Buttons that need a permission stay disabled (`{% if 'x.y' in permisos %}`).
- `url_for(...)` for links/static; consistent block structure.

## Iterations

Work in 2–3 iterations (1: naming/readability, 2: structure/complexity, 3: polish). **After each**,
run the verification:

```bash
pytest
python -m compileall -q web app.py
python -c "import jinja2, pathlib; env=jinja2.Environment(); [env.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('templates').rglob('*.html')]; print('templates OK')"
```

## Deliverables

Per iteration: scope, changes (what/why), files affected, and suggestions not applied (with reason).

When ready, start with **Iteration 1**.
