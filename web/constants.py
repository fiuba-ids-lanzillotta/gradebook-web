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
