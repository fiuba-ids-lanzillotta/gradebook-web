"""Helpers compartidos para interpretar las respuestas de la API (gradebook-api)."""

_MENSAJE_SESION_EXPIRADA = 'Sesión expirada. Volvé a iniciar sesión.'


def mensaje_error_api(response) -> str:
    """Extrae un mensaje legible del cuerpo de error de la API, o uno genérico."""
    try:
        datos = response.json()
        errores = datos.get('errors') or []

        if errores:
            textos = [
                error.get('description') or error.get('message') or ''
                for error in errores
            ]

            return ' '.join(texto for texto in textos if texto) or 'Error de validación.'
    except Exception:
        pass

    return f'Error del servidor (HTTP {response.status_code}).'


def respuesta_no_autorizada(response) -> dict | None:
    """Si la API respondió 401/403, arma el resultado de sesión expirada; si no, None."""
    if response.status_code in (401, 403):
        return {'ok': False, 'error': _MENSAJE_SESION_EXPIRADA, 'unauthorized': True}

    return None
