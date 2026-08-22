"""Consumo de gradebook-api para el listado de alumnos de una cursada."""
import csv
import io
import logging
from urllib.parse import parse_qs, urlparse

import requests

from web.constants import API_BASE_URL, CURSADA_ANIO, CURSADA_CUATRIMESTRE, api_headers
from web.services.respuestas_api import mensaje_error_api, respuesta_no_autorizada

logger = logging.getLogger(__name__)

CSV_HEADER = ['Legajo', 'Alumno', 'Email']
LIMITE_BUSQUEDA_AMPLIA = 500


def interpretar_busqueda(q: str) -> dict:
    """Traduce el buscador único a filtros de la API.

    - Solo dígitos → padron
    - Contiene @ → email
    - 'Apellido, Nombre' → apellido + nombre
    - Letras → marca nombre_completo (unión nombre OR apellido)
    """
    consulta = (q or '').strip()
    if not consulta:
        return {}

    if '@' in consulta:
        return {'email': consulta}

    compacto = consulta.replace(' ', '')
    if compacto.isdigit():
        return {'padron': consulta}

    if ',' in consulta:
        apellido, nombre = consulta.split(',', 1)
        filtros = {}
        if apellido.strip():
            filtros['apellido'] = apellido.strip()
        if nombre.strip():
            filtros['nombre'] = nombre.strip()
        return filtros

    return {'nombre_completo': consulta}


def listar_de_cursada(token: str, q: str = '', offset: int = 0, limit: int = 10) -> dict:
    """Lista alumnos de la cursada hardcodeada, con búsqueda y paginado."""
    filtros = interpretar_busqueda(q)

    if filtros.get('nombre_completo'):
        return _listar_por_nombre_completo(
            token, filtros['nombre_completo'], offset, limit
        )

    return _pedir_pagina(token, filtros, offset, limit)


def _pedir_pagina(token: str, filtros: dict, offset: int, limit: int) -> dict:
    params = {
        'anio': CURSADA_ANIO,
        'cuatrimestre': CURSADA_CUATRIMESTRE,
        '_offset': offset,
        '_limit': limit,
    }
    for clave in ('nombre', 'apellido', 'padron', 'email'):
        if filtros.get(clave):
            params[clave] = filtros[clave]

    try:
        response = requests.get(
            f'{API_BASE_URL}/estudiantes',
            params=params,
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=15,
        )
    except requests.exceptions.ConnectionError:
        logger.error(f"No se pudo conectar con la API en {API_BASE_URL}")
        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}
    except Exception as error:
        logger.error(f"Error al listar estudiantes: {error}")
        return {'ok': False, 'error': 'Ocurrió un error al cargar el listado.'}

    no_autorizada = respuesta_no_autorizada(response)
    if no_autorizada:
        return no_autorizada

    if response.status_code == 204:
        return {'ok': True, 'estudiantes': [], 'links': {}, 'offset': offset, 'limit': limit}

    if response.status_code != 200:
        return {'ok': False, 'error': mensaje_error_api(response)}

    datos = response.json() or {}
    return {
        'ok': True,
        'estudiantes': datos.get('estudiantes') or [],
        'links': datos.get('_links') or {},
        'offset': offset,
        'limit': limit,
    }


def _listar_por_nombre_completo(token: str, consulta: str, offset: int, limit: int) -> dict:
    """Une ilike de nombre y de apellido (la API solo AND por campo)."""
    por_apellido = _pedir_pagina(
        token, {'apellido': consulta}, 0, LIMITE_BUSQUEDA_AMPLIA
    )
    if not por_apellido.get('ok'):
        return por_apellido

    por_nombre = _pedir_pagina(
        token, {'nombre': consulta}, 0, LIMITE_BUSQUEDA_AMPLIA
    )
    if not por_nombre.get('ok'):
        return por_nombre

    vistos = {}
    for estudiante in por_apellido['estudiantes'] + por_nombre['estudiantes']:
        vistos[estudiante['id']] = estudiante

    ordenados = sorted(
        vistos.values(),
        key=lambda est: ((est.get('apellido') or ''), (est.get('nombre') or '')),
    )
    pagina = ordenados[offset: offset + limit]
    total = len(ordenados)
    links = _links_locales(offset, limit, total)

    return {
        'ok': True,
        'estudiantes': pagina,
        'links': links,
        'offset': offset,
        'limit': limit,
    }


def _links_locales(offset: int, limit: int, total: int) -> dict:
    """Arma _links compatibles cuando paginamos en el web (búsqueda por nombre)."""
    links = {'_first': {'_offset': 0}}
    if offset > 0:
        links['_prev'] = {'_offset': max(offset - limit, 0)}
    if offset + limit < total:
        links['_next'] = {'_offset': offset + limit}
    ultimo = 0 if total == 0 else ((total - 1) // limit) * limit
    if offset < ultimo:
        links['_last'] = {'_offset': ultimo}
    return links


def paginas_desde_links(links: dict, offset: int, limit: int) -> dict:
    """Calcula página actual y total a partir de _links (href de la API o offsets locales)."""
    pagina_actual = (offset // limit) + 1 if limit else 1
    ultimo_offset = _offset_de_link(links.get('_last'))
    if ultimo_offset is None:
        total_paginas = pagina_actual
        if links.get('_next'):
            total_paginas = pagina_actual + 1
    else:
        total_paginas = (ultimo_offset // limit) + 1

    return {
        'actual': pagina_actual,
        'total': max(total_paginas, 1),
        'offset': offset,
        'limit': limit,
    }


def _offset_de_link(link) -> int | None:
    if not link:
        return None
    if isinstance(link, dict) and '_offset' in link and 'href' not in link:
        return int(link['_offset'])
    href = (link or {}).get('href') if isinstance(link, dict) else None
    if not href:
        return None
    valores = parse_qs(urlparse(href).query).get('_offset') or []
    if not valores:
        return None
    return int(valores[0])


def crear_estudiante(token: str, datos: dict) -> dict:
    """POST /estudiantes. Password inicial = padrón (igual que el CSV)."""
    body = {
        'nombre': datos.get('nombre', '').strip(),
        'apellido': datos.get('apellido', '').strip(),
        'padron': datos.get('padron', '').strip(),
        'email': datos.get('email', '').strip(),
        'password': datos.get('padron', '').strip(),
    }
    return _escribir('post', f'{API_BASE_URL}/estudiantes', token, json=body, ok=201)


def actualizar_estudiante(token: str, estudiante_id: int, datos: dict) -> dict:
    """PUT /estudiantes/{id}. Reenvía el padrón (la API lo exige)."""
    body = {
        'nombre': datos.get('nombre', '').strip(),
        'apellido': datos.get('apellido', '').strip(),
        'padron': datos.get('padron', '').strip(),
        'email': datos.get('email', '').strip(),
    }
    return _escribir('put', f'{API_BASE_URL}/estudiantes/{estudiante_id}', token, json=body, ok=200)


def cambiar_estado(token: str, estudiante_id: int, estado: str, motivo: str | None = None) -> dict:
    """POST /estudiantes/{id}/baja  {estado, motivo?}."""
    body = {'estado': estado}
    if estado == 'baja':
        body['motivo'] = (motivo or '').strip()
    return _escribir('post', f'{API_BASE_URL}/estudiantes/{estudiante_id}/baja', token, json=body, ok=200)


def importar_csv(token: str, archivo) -> dict:
    """POST /estudiantes/csv (multipart, campo archivo)."""
    try:
        response = requests.post(
            f'{API_BASE_URL}/estudiantes/csv',
            files={'archivo': (archivo.filename, archivo.stream, archivo.mimetype or 'text/csv')},
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=60,
        )
    except requests.exceptions.ConnectionError:
        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}
    except Exception as error:
        logger.error(f"Error al importar CSV: {error}")
        return {'ok': False, 'error': 'Ocurrió un error al publicar el CSV.'}

    no_autorizada = respuesta_no_autorizada(response)
    if no_autorizada:
        return no_autorizada

    if response.status_code == 201:
        return {'ok': True, 'resumen': response.json()}

    return {'ok': False, 'error': mensaje_error_api(response)}


def exportar_csv(token: str) -> dict:
    """
    Descarga el padrón en el mismo formato SIU que el import (Legajo;Alumno;Email).

    Primero intenta GET /estudiantes/csv (ids-api: GET /cronograma/csv → text/csv).
    Si la API todavía no lo expone, lo arma recorriendo el GET paginado.
    """
    try:
        response = requests.get(
            f'{API_BASE_URL}/estudiantes/csv',
            params={'anio': CURSADA_ANIO, 'cuatrimestre': CURSADA_CUATRIMESTRE},
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=30,
        )
        if response.status_code == 200 and (response.headers.get('Content-Type') or '').startswith('text/csv'):
            return {'ok': True, 'contenido': response.content, 'nombre': _nombre_archivo()}
        no_autorizada = respuesta_no_autorizada(response)
        if no_autorizada:
            return no_autorizada
    except requests.exceptions.ConnectionError:
        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}
    except Exception as error:
        logger.error(f"Error al pedir CSV a la API: {error}")

    todos = _listar_todos(token)
    if not todos.get('ok'):
        return todos

    return {
        'ok': True,
        'contenido': _serializar_csv_siu(todos['estudiantes']).encode('utf-8-sig'),
        'nombre': _nombre_archivo(),
    }


def _nombre_archivo() -> str:
    return f'alumnos-{CURSADA_ANIO}-C{CURSADA_CUATRIMESTRE}.csv'


def _listar_todos(token: str) -> dict:
    todos = []
    offset = 0
    limit = 100
    while True:
        pagina = _pedir_pagina(token, {}, offset, limit)
        if not pagina.get('ok'):
            return pagina
        lote = pagina['estudiantes']
        todos.extend(lote)
        if not pagina['links'].get('_next') or not lote:
            break
        offset += limit
    return {'ok': True, 'estudiantes': todos}


def _serializar_csv_siu(estudiantes: list[dict]) -> str:
    """Mismo formato que importar_estudiantes_csv: Legajo;Alumno;Email."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=';', lineterminator='\r\n')
    writer.writerow(CSV_HEADER)
    for estudiante in estudiantes:
        alumno = f"{estudiante.get('apellido') or ''}, {estudiante.get('nombre') or ''}"
        writer.writerow([
            estudiante.get('padron') or '',
            alumno,
            estudiante.get('email') or '',
        ])
    return buffer.getvalue()


def _escribir(metodo: str, url: str, token: str, json=None, ok: int = 200) -> dict:
    try:
        cliente = getattr(requests, metodo)
        response = cliente(
            url,
            json=json,
            headers=api_headers({'Authorization': f'Bearer {token}'}),
            timeout=15,
        )
    except requests.exceptions.ConnectionError:
        return {'ok': False, 'error': 'No se pudo conectar con el servidor. Intentá más tarde.'}
    except Exception as error:
        logger.error(f"Error al escribir {url}: {error}")
        return {'ok': False, 'error': 'Ocurrió un error al guardar.'}

    no_autorizada = respuesta_no_autorizada(response)
    if no_autorizada:
        return no_autorizada

    if response.status_code == ok:
        return {'ok': True, 'datos': response.json() if response.content else {}}

    return {'ok': False, 'error': mensaje_error_api(response)}