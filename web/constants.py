import os
from dotenv import load_dotenv

load_dotenv()

# URL base de la API del backend (gradebook-api). Configurable por variable de entorno.
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/gradebook_api')

# API key para consumir gradebook-api (debe coincidir con la API_KEY del backend).
# Si está vacía, no se envía el header (la API queda pública).
API_KEY = os.getenv('API_KEY', '')


def api_headers(extra: dict | None = None) -> dict:
    """Headers para las requests a gradebook-api; agrega X-API-Key si está configurada."""
    headers = dict(extra or {})

    if API_KEY:
        headers['X-API-Key'] = API_KEY

    return headers

# Site key PÚBLICA de reCAPTCHA v2. Se renderiza en el widget del login. Si está
# vacía, el login no muestra el captcha. El secret NO va en el frontend: la
# verificación server-side la hace gradebook-api con su RECAPTCHA_SECRET.
RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY', '').strip()

# Código de la materia de la cátedra. Se usa para resolver la cursada vigente
# contra la API (GET /cursadas?codigo=MATERIA_CODIGO).
MATERIA_CODIGO = 'TB022'

# Año/cuatrimestre de respaldo si la API no devuelve una cursada vigente.
CURSADA_ANIO = '2026'
CURSADA_CUATRIMESTRE = '2'

ROL_SUPER_ADMIN = 'super_admin'

PERMISO_DOCENTES_LEER         = 'docentes.leer'
PERMISO_DOCENTES_GESTIONAR    = 'docentes.gestionar'
PERMISO_ESTUDIANTES_LEER      = 'estudiantes.leer'
PERMISO_ESTUDIANTES_CREAR     = 'estudiantes.crear'
PERMISO_ESTUDIANTES_MODIFICAR  = 'estudiantes.modificar'
PERMISO_ESTUDIANTES_ELIMINAR  = 'estudiantes.eliminar'
PERMISO_ESTUDIANTES_REACTIVAR = 'estudiantes.reactivar'
PERMISO_CURSADAS_LEER         = 'cursadas.leer'
PERMISO_CURSADAS_CREAR        = 'cursadas.crear'
PERMISO_CURSADAS_MODIFICAR    = 'cursadas.modificar'
PERMISO_ASISTENCIAS_LEER      = 'asistencias.leer'
PERMISO_ASISTENCIAS_GESTIONAR = 'asistencias.gestionar'
PERMISO_NOTAS_LEER            = 'notas.leer'
PERMISO_EVALUACIONES_LEER     = 'evaluaciones.leer'
PERMISO_ROLES_LEER            = 'roles.leer'
PERMISO_ROLES_GESTIONAR       = 'roles.gestionar'
PERMISO_PERMISOS_ASIGNAR      = 'permisos.asignar'