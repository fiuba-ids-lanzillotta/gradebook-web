---
name: verify
description: Run the frontend's verification (tests + Python syntax check + Jinja template parse)
allowed-tools:
  - read
  - exec
permissions:
  allow:
    - Read(**)
    - Exec(python*)
    - Exec(pytest*)
---

Run the verification and report the result. Verification = pytest + a Python syntax check + a
Jinja template parse. Do not change code; if something fails, report where.

## Steps

0. If the dev deps aren't installed yet (`pytest` missing): `pip install -r requirements-dev.txt`.

1. Run the tests (services and routes with `requests` mocked; no network, no `gradebook-api`
   needed — fixtures `respuesta_falsa`/`cargar_json` in `conftest.py`, JSON mocks under
   `tests/resources/json/`):
   ```bash
   pytest
   ```

2. Compile the Python:
   ```bash
   python -m compileall -q web app.py
   ```

3. Parse the Jinja templates (catches template syntax errors without needing the app running):
   ```bash
   python -c "import jinja2, pathlib; env=jinja2.Environment(); [env.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('templates').rglob('*.html')]; print('templates OK')"
   ```

4. (Optional) Smoke test: start the app (`python app.py`, port 5001) and load `/admin/login`. To
   actually log in you need `gradebook-api` reachable at `API_BASE_URL` (port 5000).

## Report

- Tests: passed count / failures (test name).
- Compile: OK / errors (file + line).
- Templates: OK / parse error (file).
- If everything is green, say so explicitly.
