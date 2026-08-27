# gradebook-web

Proyecto **base** de un frontend web server-rendered en **Flask + Jinja2**, pensado como punto de
partida. Renderiza páginas públicas y un panel de administración, y consume el backend
**`gradebook-api`** por HTTP. No tiene base de datos propia. Sigue el mismo estilo y arquitectura
que el resto de los proyectos del workspace (basado en `ids-web`).

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
├── setup_virtualenv.bat/.sh     # Scripts de setup con virtualenv
├── setup_pipenv.bat/.sh         # Scripts de setup con pipenv
├── AGENTS.md / README.md / LICENSE
├── .gitignore / .gitattributes
│
├── web/
│   ├── constants.py             # API_BASE_URL, API_KEY, api_headers(), RECAPTCHA_SITE_KEY, MATERIA_CODIGO
│   ├── auth_sesion.py            # Helpers de sesión: admin_required, es_super_admin, puede_dar_baja
│   ├── routes/                  # Blueprints (presentación / flujo)
│   │   ├── site/                #   Zona pública (sin prefijo): home
│   │   └── admin/               #   Zona admin (/admin): auth, panel, docentes
│   └── services/                # Llamadas HTTP a gradebook-api
│       ├── auth.py              #   login
│       ├── docentes.py          #   CRUD de docentes (listar, crear, actualizar, eliminar, permisos)
│       ├── permisos.py         #   Catálogo de permisos
│       ├── estudiantes.py       #   CRUD de estudiantes
│       ├── asistencia.py        #   Gestión de asistencia
│       ├── cursos.py            #   Cursadas
│       └── respuestas_api.py    #   helpers para interpretar errores / 401-403
│
├── templates/
│   ├── base.html                # Layout base (navbar, bloques)
│   ├── 404.html
│   ├── site/                    # inicio.html, items.html
│   └── admin/                   # login.html, panel.html, items.html
├── static/
│   ├── css/                     # common.css, site.css, admin.css
│   └── js/                      # main.js (modales de items + toggle de contraseña)
└── tests/                       # Tests (pytest): auth, items, rutas, respuestas_api
    └── resources/json/          # Mocks JSON de las respuestas de la API
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
setup_virtualenv.bat          # Windows
chmod +x setup_virtualenv.sh && ./setup_virtualenv.sh   # Linux / macOS
```

**Con pipenv:**

```bash
setup_pipenv.bat              # Windows
chmod +x setup_pipenv.sh && ./setup_pipenv.sh           # Linux / macOS
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

## Páginas

| Ruta            | Auth  | Descripción                                             |
|-----------------|-------|---------------------------------------------------------|
| `/`             | —     | Inicio (landing del proyecto base).                     |
| `/admin/login`  | —     | Login del panel (valida contra `POST /login`).          |
| `/admin/`       | admin | Panel de administración (listado de alumnos).           |
| `/admin/docentes` | admin | Gestión de docentes (listar, crear, editar, eliminar, permisos). |

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
no localhost) y `API_KEY` (la misma que `gradebook-api`).
