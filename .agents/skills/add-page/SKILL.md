---
name: add-page
description: Add a page/route to the frontend (Flask blueprint + Jinja template, optionally consuming gradebook-api)
argument-hint: "[zone and page, e.g. 'site/entregas' or 'admin/equipos']"
allowed-tools:
  - read
  - edit
  - write
  - grep
  - glob
  - exec
permissions:
  allow:
    - Read(**)
    - Exec(python -m compileall*)
    - Exec(python*)
    - Exec(pytest*)
  ask:
    - Write(web/**)
    - Write(templates/**)
    - Write(tests/**)
---

Add a new page: **$ARGUMENTS**. Read `AGENTS.md` first and mirror the existing pages.

This app has two zones: **`site/` is the student backoffice** (requires login) and **`admin/` is
the docente backoffice** (requires docente role + permissions). There are no public pages.

## Checklist

1. **Route** in the right blueprint:
   - Student → `web/routes/site/<pagina>.py` (registered in `web/routes/site/__init__.py`),
     protected with `@login_required` (docentes get bounced to the admin panel).
   - Docente → `web/routes/admin/<pagina>.py` (registered in `web/routes/admin/__init__.py`),
     protected with `@admin_required` and gated by permission: `tiene_permiso(PERMISO_*)` +
     `redirigir_sin_permiso()` (see `docentes.py` / `asistencia.py` for the pattern).
   Keep the route thin: it renders a template and delegates any API call to a service.

2. **Template**:
   - Student → `templates/site/<pagina>.html` extending `base.html`.
   - Docente → `templates/admin/<pagina>.html` extending `admin/base_admin.html`, and render it
     with `**contexto_admin('<solapa>')` (from `web/routes/admin/panel.py`) so the sidebar works.
   Guard optional/empty data with `{% if %}` so it renders cleanly when the API has no data.

3. **Sidebar solapa** (docente pages only): add the entry to `SOLAPAS` in
   `web/routes/admin/panel.py`, map its permission in `SOLAPA_PERMISO` (keys live in
   `web/constants.py` as `PERMISO_*`), and add the `url_for` branch for the new clave in
   `templates/admin/base_admin.html`.

4. **Service** (only if the page needs data from `gradebook-api`): add functions in
   `web/services/<recurso>.py` calling the API with `requests` + `api_headers(...)`. For admin
   calls send `Authorization: Bearer {session['token']}` (merged via `api_headers`) and use
   `respuesta_no_autorizada` / `mensaje_error_api` from `web/services/respuestas_api.py` so
   401/403 return `{'unauthorized': True}` and the route can clear the session.

5. **Navigation** (student pages only): add the link in `templates/base.html` navbar with
   `url_for('web.site.<x>...')` if the page belongs in the menu.

6. **Tests**: add `tests/test_<recurso>.py` (routes via `app.test_client()`, `requests` mocked —
   see `conftest.py` fixtures `respuesta_falsa` / `cargar_json`) plus JSON mocks under
   `tests/resources/json/<dominio>/`.

7. **Verify:**
   ```bash
   pytest
   python -m compileall -q web app.py
   python -c "import jinja2, pathlib; env=jinja2.Environment(); [env.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('templates').rglob('*.html')]; print('templates OK')"
   ```

Report the files added/changed. Note: `MATERIA_CODIGO` and the `CURSADA_*` fallbacks live in
`web/constants.py`; the diseño de referencia está en Figma (IDS-Lanzillota, páginas "backoffice
alumno" y "backoffice docente").
