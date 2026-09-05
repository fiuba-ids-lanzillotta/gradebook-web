"""Consumo de la API (gradebook-api) para la autenticación del panel de admin."""
import logging
import requests

from web.constants import API_BASE_URL, api_headers

logger = logging.getLogger(__name__)


def autenticar(email: str, password: str, recaptcha_token: str = '') -> dict:
    """Autentica las credenciales contra la API.

    Retorna {'ok': True, 'token': str, 'usuario': dict} si son correctas,
    o {'ok': False, 'error': str} con un mensaje para mostrar al usuario.
    """
    try:
        response = requests.post(
            f'{API_BASE_URL}/login',
            json={'email': email, 'password': password, 'recaptcha_token': recaptcha_token,},
            headers=api_headers(),
            timeout=10,
        )

        if response.status_code == 200:
            datos = response.json()
            
            return {'ok': True, 'token': datos['token'], 'usuario': datos['usuario']}

        if response.status_code == 401:
            return {'ok': False, 'error': 'Credenciales inválidas.'}
        if response.status_code == 400:
            try:
                cuerpo = response.json()
            except ValueError:
                cuerpo = {}
            errores = cuerpo.get('errors') or []
            codigo = errores[0].get('code') if errores else None
            if codigo == 'recaptcha.missing':
                return {'ok': False, 'error': 'Rellená el reCAPTCHA.'}
            if codigo == 'recaptcha.invalid':
                return {'ok': False, 'error': 'El reCAPTCHA no es válido. Volvé a intentarlo.'}
        return {'ok': False, 'error': f'Error del servidor (HTTP {response.status_code}).'}
        
    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}

    except Exception as error:
        logger.error(f"Error al autenticar: {error}")

        return {'ok': False, 'error': 'Ocurrió un error al iniciar sesión.'}

def obtener_identidad(token: str) -> dict:
    """GET /me. Identidad con permisos efectivos, o {} si falla."""
    try:
        response = requests.get(
            f'{API_BASE_URL}/me',
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {}
    except Exception as error:
        logger.error(f"Error al obtener identidad: {error}")

        return {}

    if response.status_code != 200:
        return {}

    return response.json() or {}

def solicitar_recuperacion(email: str) -> dict:
    """Pide a la API el envío del link de recuperación.

    La API responde igual exista o no el email (anti-enumeración): retornamos
    {'ok': True} salvo error de conexión, para mostrar siempre el mismo mensaje.
    """
    try:
        requests.post(
            f'{API_BASE_URL}/password-reset/solicitar',
            json={'email': email},
            headers=api_headers(),
            timeout=10,
        )

        return {'ok': True}

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}

    except Exception as error:
        logger.error(f"Error al solicitar recuperación: {error}")

        return {'ok': False, 'error': 'Ocurrió un error. Intentá más tarde.'}


def confirmar_recuperacion(token: str, password: str) -> dict:
    """Confirma el reset en la API con el token de un solo uso y la nueva contraseña."""
    try:
        response = requests.post(
            f'{API_BASE_URL}/password-reset/confirmar',
            json={'token': token, 'password': password},
            headers=api_headers(),
            timeout=10,
        )

        if response.status_code == 200:
            return {'ok': True}

        if response.status_code == 400:
            return {'ok': False, 'error': 'El enlace no es válido, ya se usó o expiró. Solicitá uno nuevo.'}

        return {'ok': False, 'error': f'Error del servidor (HTTP {response.status_code}).'}

    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}

    except Exception as error:
        logger.error(f"Error al confirmar recuperación: {error}")

        return {'ok': False, 'error': 'Ocurrió un error. Intentá más tarde.'}
