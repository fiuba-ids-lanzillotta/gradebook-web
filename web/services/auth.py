"""Consumo de la API (gradebook-api) para la autenticación del panel de admin."""
import logging
import requests

from web.constants import API_BASE_URL, api_headers

logger = logging.getLogger(__name__)


def autenticar(usuario: str, password: str) -> dict:
    """Autentica las credenciales contra la API.

    Retorna {'ok': True, 'token': str, 'usuario': dict} si son correctas,
    o {'ok': False, 'error': str} con un mensaje para mostrar al usuario.
    """
    try:
        response = requests.post(
            f'{API_BASE_URL}/login',
            json={'usuario': usuario, 'password': password},
            headers=api_headers(),
            timeout=10,
        )

        if response.status_code == 200:
            datos = response.json()
            return {'ok': True, 'token': datos['token'], 'usuario': datos['usuario']}

        if response.status_code == 401:
            return {'ok': False, 'error': 'Usuario o contraseña incorrectos.'}

        return {'ok': False, 'error': f'Error del servidor (HTTP {response.status_code}).'}

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}

    except Exception as error:
        logger.error(f"Error al autenticar: {error}")

        return {'ok': False, 'error': 'Ocurrió un error al iniciar sesión.'}
