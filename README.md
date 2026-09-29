# gradebook-web

Proyecto **base** de un frontend web server-rendered en **Flask + Jinja2**, pensado como punto de
partida. Tiene dos zonas: **`site/`** es el backoffice del alumno (requiere login) y **`/admin`**
es el backoffice del docente (requiere login + rol docente, con permisos por sección). Consume el
backend **`gradebook-api`** por HTTP. No tiene base de datos propia. Sigue el mismo estilo y
arquitectura que el resto de los proyectos del workspace (basado en `ids-web`).

## Tecnologías

- **Python 3.10+**
- **Flask 3.0.3** + **Jinja2** (server-side rendering)
- **requests** (consumo de la API)
- **python-dotenv** (variables de entorno)

Estilo **funcional** (sin clases, datos como `dict`/`list`) y separación en capas
**routes → services**. Las rutas no hacen HTTP; los services encapsulan las llamadas a la API.

## Arquitectura

```
Flujo de una request:

  Navegador
     |
     |  HTTP (HTML)
     v
  Flask (gradebook-web, puerto 5001)
     |   - routes (blueprints): presentación y flujo
     |   - services: llaman a gradebook-api con requests (+ header X-API-Key)
     |     · lecturas públicas: degradan con gracia si la API no responde
     |     · escrituras admin: envían Authorization: Bearer <jwt>
     v
  gradebook-api (puerto 5000) → Supabase
```

## Estructura del proyecto

```
gradebook-web/
├── app.py                       # Entry point Flask (puerto 5001, registra el blueprint web)
├── requirements.txt             # Dependencias Python
├── requirements-dev.txt         # Dependencias de desarrollo (pytest)
├── vercel.json                  # Configuración de deploy en Vercel
├── pytest.ini / conftest.py     # Configuración de los tests
├── .env.example                 # Template de variables de entorno
├── scripts/                     # setup_virtualenv / setup_pipenv (.bat/.sh)
├── AGENTS.md / README.md / LICENSE
├── .gitignore / .gitattributes
│
├── web/
│   ├── constants.py             # API_BASE_URL, API_KEY, api_headers(), RECAPTCHA_SITE_KEY,
│   │                            #   MATERIA_CODIGO, fallbacks CURSADA_*, códigos PERMISO_*
│   ├── auth_sesion.py            # Helpers de sesión: login_required, admin_required, tiene_permiso
│   ├── routes/                  # Blueprints (presentación / flujo)
│   │   ├── site/                #   Zona alumno (sin prefijo, login): home, items (ejemplo)
│   │   └── admin/               #   Backoffice docente (/admin): auth, panel, asistencia,
│   │                            #   docentes, items (ejemplo)
│   └── services/                # Llamadas HTTP a gradebook-api
│       ├── auth.py              #   login, recuperación de contraseña, identidad
│       ├── docentes.py          #   CRUD de docentes (listar, crear, actualizar, eliminar, permisos)
│       ├── permisos.py         #   Catálogo de permisos
│       ├── estudiantes.py       #   CRUD de estudiantes + CSV
│       ├── asistencia.py        #   Gestión de asistencia
│       ├── cursos.py            #   Cursadas
│       ├── items.py            #   Recurso de ejemplo
│       └── respuestas_api.py    #   helpers para interpretar errores / 401-403
│
├── templates/
│   ├── base.html                # Layout base (navbar, bloques) — site + auth
│   ├── 404.html
│   ├── site/                    # inicio.html, items.html
│   └── admin/                   # base_admin.html (layout con sidebar de solapas), login.html,
│                                #   recuperar.html, cambiar_contrasena.html, panel.html,
│                                #   asistencia.html, asistencia_listado.html, docentes.html,
│                                #   items.html
├── static/
│   ├── css/                     # common.css, site.css, admin.css
│   └── js/                      # main.js (modales, asistencia, toggle de contraseña)
├── tests/                       # Tests (pytest): auth, cursos, estudiantes, items, rutas,
│   └── resources/json/          #   respuestas_api — mocks JSON de las respuestas de la API
└── .agents/skills/              # Skills para agentes (add-page, verify, sync-docs, ...)
```

## Configuración

### 1. Variables de entorno

Copiá `.env.example` a `.env` y completá los valores:

```bash
cp .env.example .env        # Linux / macOS
copy .env.example .env      # Windows
```

| Variable       | Descripción                                                                        |
|----------------|------------------------------------------------------------------------------------|
| `SECRET_KEY`   | Clave con la que Flask firma las sesiones (propia de gradebook-web).               |
| `API_BASE_URL` | URL base de `gradebook-api` (default `http://localhost:5000/gradebook_api`).       |
| `API_KEY`      | Debe coincidir con la `API_KEY` del backend. Se envía como header `X-API-Key`. Vacío si la API es pública. |
| `RECAPTCHA_SITE_KEY` | Site key **pública** de reCAPTCHA v2 para el widget del login. El secret vive en `gradebook-api` (`RECAPTCHA_SECRET`). Vacío = login sin captcha. |

> El `.env` está en `.gitignore` y **no debe subirse al repositorio**.

Para generar una `SECRET_KEY` aleatoria:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Backend

El login del panel y el CRUD de items se validan contra `gradebook-api`. Levantá primero el backend
(ver `../gradebook-api/README.md`); las credenciales de admin viven en el `.env` de la API, no acá.

### 3. Entorno virtual, instalación y ejecución

Los scripts crean el entorno virtual, instalan las dependencias y levantan la app.

**Con virtualenv:**

```bash
scripts\setup_virtualenv.bat          # Windows
chmod +x scripts/setup_virtualenv.sh && scripts/setup_virtualenv.sh   # Linux / macOS
```

**Con pipenv:**

```bash
scripts\setup_pipenv.bat              # Windows
chmod +x scripts/setup_pipenv.sh && scripts/setup_pipenv.sh           # Linux / macOS
```

También manualmente:

```bash
python -m venv .venv
source .venv/bin/activate     # Linux / macOS
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

La app queda disponible en `http://localhost:5001`.

### 4. Probar desde un celular

Como las llamadas a `gradebook-api` las hace el servidor (server-side), el celular solo
necesita alcanzar `gradebook-web`; la API puede seguir en `localhost:5000` sin exponerse.

Con la app corriendo en `:5001`, exponela con un túnel:

```bash
ngrok http 5001                # o
npx localtunnel --port 5001
```

Abrí la URL generada (`https://<algo>.ngrok.io` / `.loca.lt`) en el celular. No hay que tocar
el `.env`: `API_BASE_URL` sigue siendo `localhost` porque la llamada sale del servidor, no del
browser del celular.

Notas:

- Los planes gratuitos muestran una página intermedia en la primera visita (ngrok) o piden la
  IP pública como "password" del túnel (localtunnel).
- Si usás una **site key real de reCAPTCHA**, el dominio del túnel tiene que estar autorizado
  en la consola de reCAPTCHA — la test key de Google funciona en cualquier dominio.
- Alternativa sin túnel en la misma Wi-Fi: `flask --app app run --host 0.0.0.0 --port 5001` y
  el celular entra a `http://<IP-de-la-PC>:5001` (con `python app.py` solo bindea a localhost).

## Páginas

| Ruta                        | Auth     | Descripción                                                          |
|-----------------------------|----------|----------------------------------------------------------------------|
| `/`                         | alumno   | Inicio de la zona alumno (hoy: landing base, pendiente "Novedades").   |
| `/items`                    | alumno   | Recurso de ejemplo `items`.                                          |
| `/admin/login`              | —        | Login compartido (valida contra `POST /login` de la API + reCAPTCHA). |
| `/admin/logout`             | —        | Cierra la sesión.                                                    |
| `/admin/recuperar`          | —        | Solicita mail de recuperación de contraseña.                         |
| `/admin/cambiar-contrasena` | —        | Define contraseña nueva desde el link del mail (`?token=`).          |
| `/admin/`                   | docente  | Listado de alumnos del cuatrimestre: alta, edición, baja/abandono, CSV.|
| `/admin/docentes`           | docente* | Gestión de docentes (listar, crear, editar, desactivar, permisos).    |
| `/admin/asistencia`         | docente* | Toma de asistencia del día (QR / código / padrón).                   |
| `/admin/asistencia/listado` | docente* | Asistencias por clase (filtros por estado y búsqueda).               |

\* Las pantallas de docente están gateadas por permisos (`PERMISO_*` en `web/constants.py`); el
sidebar solo muestra las solapas habilitadas. Solapas declaradas pero sin pantalla todavía:
dashboards, categorías, registros, entregas, vista general (ver `.agents/skills/add-page`).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Los tests mockean `requests`, por lo que **no requieren** `gradebook-api` corriendo ni acceso a
red. Las respuestas de la API se guardan como mocks JSON en `tests/resources/json/`.

## Deploy

Vercel (`vercel.json` → función Python sobre `app.py`, `includeFiles: "**"`). Las variables de
entorno se configuran en el dashboard de Vercel: `SECRET_KEY`, `API_BASE_URL` (la API desplegada,
no localhost), `API_KEY` (la misma que `gradebook-api`) y `RECAPTCHA_SITE_KEY` (par público del
`RECAPTCHA_SECRET` de la API).
