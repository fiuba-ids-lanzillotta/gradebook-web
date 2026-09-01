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

CARGOS = ('Profesor', 'Ayudante', 'Colaborador')

ESTADO_INSCRIPCION_ETIQUETA = {
    'cursando': 'Cursando',
    'abandono': 'Abandonó',
    'baja': 'Se dió de baja',
}

ESTADO_ASISTENCIA_ETIQUETA = {
    'presente': 'Presente',
    'pendiente': 'Pendiente',
    'ausente': 'Ausente',
}

METODO_ASISTENCIA_ETIQUETA = {
    'qr': 'QR',
    'manual': 'Código',
    'padron': 'Padrón',
}

ESTADOS_ASISTENCIA_FILTRO = ('presente', 'pendiente', 'ausente')