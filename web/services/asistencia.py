"""Consumo de gradebook-api para tomar y marcar asistencia (QR / código / padrón)."""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from web.constants import API_BASE_URL, CURSADA_ANIO, CURSADA_CUATRIMESTRE, MATERIA_CODIGO, api_headers
from web.services.cursos import obtener_cursada_vigente
from web.services.respuestas_api import mensaje_error_api, respuesta_no_autorizada

logger = logging.getLogger(__name__)

TZ_CATEDRA = ZoneInfo('America/Argentina/Buenos_Aires')


def fecha_hoy() -> str:
    """Fecha de la toma: siempre hoy, en hora de Argentina."""
    return datetime.now(TZ_CATEDRA).date().isoformat()


def crear_clase_hoy(token: str) -> dict:
    """POST /cursadas/{id}/clases con la fecha de hoy (idempotente)."""
    cursada = obtener_cursada_vigente(token)
    cursada_id = cursada.get('id')

    if not cursada_id:
        return {'ok': False, 'error': 'No hay cursada vigente para tomar asistencia.'}

    resultado = _pedir(
        token,
        'POST',
        f'/cursadas/{cursada_id}/clases',
        json_body={'fecha': fecha_hoy()},
        ok=(200, 201),
        timeout=60,
    )

    if not resultado.get('ok'):
        return resultado

    datos = resultado.get('datos') or {}
    clase = datos.get('clase') or {}

    return {
        'ok': True,
        'clase': clase,
        'clase_id': clase.get('id'),
        'total_estudiantes': datos.get('total_estudiantes', 0),
        'generados': datos.get('generados', 0),
        'fecha': fecha_hoy(),
    }


def enviar_qrs(token: str, clase_id: int) -> dict:
    """POST /clases/{id}/enviar-qrs: un lote. El front lo llama en bucle."""
    resultado = _pedir(
        token,
        'POST',
        f'/clases/{clase_id}/enviar-qrs',
        ok=(200,),
        timeout=60,
    )

    if not resultado.get('ok'):
        return resultado

    return {'ok': True, **(resultado.get('datos') or {})}


def estado_envio(token: str, clase_id: int) -> dict:
    resultado = _pedir(token, 'GET', f'/clases/{clase_id}/envio', ok=(200,))
    
    if not resultado.get('ok'):
        return resultado

    return {'ok': True, **(resultado.get('datos') or {})}


def clase_de_hoy(token: str) -> dict:
    """Busca la clase de hoy en la cursada vigente (para escanear sin volver a disparar)."""
    cursada = obtener_cursada_vigente(token)
    cursada_id = cursada.get('id')

    if not cursada_id:
        return {'ok': True, 'clase': None}

    hoy = fecha_hoy()
    offset = 0
    limit = 50
    continuar_busqueda = True

    while continuar_busqueda:
        resultado = _pedir(
            token,
            'GET',
            f'/cursadas/{cursada_id}/clases',
            params={'_offset': offset, '_limit': limit},
            ok=(200, 204),
        )

        if not resultado.get('ok'):
            return resultado

        if resultado.get('vacio'):
            return {'ok': True, 'clase': None}

        clases = (resultado.get('datos') or {}).get('clases') or []

        for clase in clases:
            if str(clase.get('fecha') or '')[:10] == hoy:
                return {'ok': True, 'clase': clase}

        links = (resultado.get('datos') or {}).get('_links') or {}

        continuar_busqueda = links.get('_next') and clases
        offset += limit

    return {'ok': True, 'clase': None}

def _cursada_para_asistencia(token: str) -> dict:
    vigente = obtener_cursada_vigente(token)

    if vigente.get('id'):
        return vigente

    resultado = _pedir(
        token,
        'GET',
        '/cursadas',
        params={'codigo': MATERIA_CODIGO, '_limit': 100},
        ok=(200, 204),
    )

    if not resultado.get('ok'):
        return resultado

    cursos = (resultado.get('datos') or {}).get('cursadas') or []

    for curso in cursos:
        if str(curso.get('anio')) == str(CURSADA_ANIO) and str(curso.get('cuatrimestre')) == str(CURSADA_CUATRIMESTRE):
            return curso

    return cursos[0] if cursos else {}

def marcar(token: str, clase_id: int, codigo: str = '', padron: str = '', manual: bool = False) -> dict:
    """POST /clases/{id}/marcar. Exactamente uno de codigo o padron."""
    cuerpo = {}

    if codigo:
        cuerpo['codigo'] = codigo

        if manual:
            cuerpo['manual'] = True
    elif padron:
        cuerpo['padron'] = padron

    resultado = _pedir(
        token,
        'POST',
        f'/clases/{clase_id}/marcar',
        json_body=cuerpo,
        ok=(200,),
    )

    if not resultado.get('ok'):
        return resultado

    return {'ok': True, **(resultado.get('datos') or {})}

def listar_clases(token: str) -> dict:
    """GET /cursadas/{id}/clases (trae estado abierta/cerrada). Más recientes primero."""
    cursada = _cursada_para_asistencia(token)

    if cursada.get('unauthorized'):
        return cursada

    cursada_id = cursada.get('id') if isinstance(cursada, dict) else None

    if not cursada_id:
        return {'ok': True, 'clases': []}

    clases = []
    offset = 0
    limit = 50

    while True:
        resultado = _pedir(
            token,
            'GET',
            f'/cursadas/{cursada_id}/clases',
            params={'_offset': offset, '_limit': limit},
            ok=(200, 204),
        )

        if not resultado.get('ok'):
            return resultado

        if resultado.get('vacio'):
            break

        lote = (resultado.get('datos') or {}).get('clases') or []
        clases.extend(lote)
        links = (resultado.get('datos') or {}).get('_links') or {}

        if not links.get('_next') or not lote:
            break

        offset += limit

    return {'ok': True, 'clases': clases}


def listar_asistencias(token: str, clase_id: int, estado: str = '', q: str = '') -> dict:
    """GET /clases/{id}/asistencias (todas las páginas)."""
    filas = []
    offset = 0
    limit = 100

    while True:
        params = {'_offset': offset, '_limit': limit}

        if estado:
            params['estado'] = estado

        if q:
            params['q'] = q

        resultado = _pedir(
            token,
            'GET',
            f'/clases/{clase_id}/asistencias',
            params=params,
            ok=(200, 204),
        )

        if not resultado.get('ok'):
            return resultado

        if resultado.get('vacio'):
            break

        lote = (resultado.get('datos') or {}).get('asistencias') or []
        filas.extend(lote)
        links = (resultado.get('datos') or {}).get('_links') or {}

        if not links.get('_next') or not lote:
            break

        offset += limit

    return {'ok': True, 'asistencias': filas}


def cerrar_clase(token: str, clase_id: int) -> dict:
    """POST /clases/{id}/cerrar: pendientes → ausente."""
    resultado = _pedir(
        token,
        'POST',
        f'/clases/{clase_id}/cerrar',
        ok=(200,),
    )

    if not resultado.get('ok'):
        return resultado

    return {'ok': True, **(resultado.get('datos') or {})}


def etiqueta_clase(clase: dict) -> str:
    fecha = str((clase or {}).get('fecha') or '')[:10]

    if len(fecha) == 10 and fecha[4] == '-' and fecha[7] == '-':
        fecha_txt = f'{fecha[8:10]}/{fecha[5:7]}/{fecha[0:4]}'
    else:
        fecha_txt = fecha or 'Sin fecha'

    titulo = str((clase or {}).get('titulo') or '').strip()

    return f'{fecha_txt} · {titulo}' if titulo else fecha_txt

def _pedir(token: str, method: str, path: str, *, json_body=None, params=None, ok=(200,), timeout=20) -> dict:
    try:
        response = requests.request(
            method,
            f'{API_BASE_URL}{path}',
            json=json_body,
            params=params,
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=timeout,
        )
    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")

        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}
    except Exception as error:
        logger.error(f"Error en {method} {path}: {error}")

        return {'ok': False, 'error': 'Ocurrió un error al hablar con el servidor.'}

    no_autorizada = respuesta_no_autorizada(response)

    if no_autorizada:
        return no_autorizada

    if response.status_code == 204:
        return {'ok': True, 'vacio': True, 'datos': {}}

    if response.status_code not in ok:
        return {
            'ok': False,
            'error': mensaje_error_api(response),
            'status': response.status_code,
        }

    try:
        datos = response.json() or {}
    except Exception:
        datos = {}
        
    return {'ok': True, 'datos': datos}