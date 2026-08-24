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

MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', '') or MAIL_USERNAME
MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'false').lower() == 'true'