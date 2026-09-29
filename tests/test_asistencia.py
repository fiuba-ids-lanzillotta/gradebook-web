import re

import requests

from web.services import asistencia
from web.services.asistencia import etiqueta_clase


def _cursada_vigente():
    return {'id': 9, 'anio': 2026, 'cuatrimestre': 2, 'vigente': True}


# --- funciones puras ---

def test_fecha_hoy_es_iso():
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', asistencia.fecha_hoy())


def test_etiqueta_clase_formatea_fecha_y_titulo():
    assert etiqueta_clase({'fecha': '2026-09-29', 'titulo': 'Clase 5'}) == '29/09/2026 · Clase 5'


def test_etiqueta_clase_sin_titulo():
    assert etiqueta_clase({'fecha': '2026-09-29'}) == '29/09/2026'


def test_etiqueta_clase_sin_fecha():
    assert etiqueta_clase({}) == 'Sin fecha'


# --- crear_clase_hoy ---

def test_crear_clase_hoy_postea_fecha_en_la_vigente(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(asistencia, 'obtener_cursada_vigente', lambda token: _cursada_vigente())
    capturado = {}

    def fake_request(method, url, json=None, **kwargs):
        capturado['method'] = method
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(201, {'clase': {'id': 4}, 'total_estudiantes': 12, 'generados': 12})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = asistencia.crear_clase_hoy('token')

    assert capturado['method'] == 'POST'
    assert capturado['url'].endswith('/cursadas/9/clases')
    assert capturado['json'] == {'fecha': asistencia.fecha_hoy()}
    assert resultado['ok'] and resultado['clase_id'] == 4
    assert resultado['total_estudiantes'] == 12


def test_crear_clase_hoy_sin_cursada_no_llama_api(monkeypatch):
    monkeypatch.setattr(asistencia, 'obtener_cursada_vigente', lambda token: {})
    llamadas = []
    monkeypatch.setattr(requests, 'request', lambda *a, **k: llamadas.append(a))

    resultado = asistencia.crear_clase_hoy('token')

    assert resultado['ok'] is False
    assert llamadas == []


# --- envío de QRs ---

def test_enviar_qrs_devuelve_datos_del_lote(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(method, url, **kwargs):
        capturado['url'] = url
        return respuesta_falsa(200, {'enviados': 10, 'pendientes': 30})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = asistencia.enviar_qrs('token', 4)

    assert capturado['url'].endswith('/clases/4/enviar-qrs')
    assert resultado == {'ok': True, 'enviados': 10, 'pendientes': 30}


def test_estado_envio_consulta_progreso(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(method, url, **kwargs):
        capturado['url'] = url
        return respuesta_falsa(200, {'enviados': 40, 'total': 40})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = asistencia.estado_envio('token', 4)

    assert capturado['url'].endswith('/clases/4/envio')
    assert resultado['ok'] and resultado['total'] == 40


# --- clase_de_hoy ---

def test_clase_de_hoy_encuentra_la_de_hoy(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(asistencia, 'obtener_cursada_vigente', lambda token: _cursada_vigente())
    clases = [{'id': 2, 'fecha': '2020-01-01'}, {'id': 5, 'fecha': asistencia.fecha_hoy()}]
    monkeypatch.setattr(requests, 'request',
                        lambda *a, **k: respuesta_falsa(200, {'clases': clases, '_links': {}}))

    resultado = asistencia.clase_de_hoy('token')

    assert resultado['ok'] and resultado['clase']['id'] == 5


def test_clase_de_hoy_sin_match_devuelve_none(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(asistencia, 'obtener_cursada_vigente', lambda token: _cursada_vigente())
    clases = [{'id': 2, 'fecha': '2020-01-01'}]
    monkeypatch.setattr(requests, 'request',
                        lambda *a, **k: respuesta_falsa(200, {'clases': clases, '_links': {}}))

    resultado = asistencia.clase_de_hoy('token')

    assert resultado['ok'] and resultado['clase'] is None


def test_clase_de_hoy_sin_cursada_no_llama_api(monkeypatch):
    monkeypatch.setattr(asistencia, 'obtener_cursada_vigente', lambda token: {})
    llamadas = []
    monkeypatch.setattr(requests, 'request', lambda *a, **k: llamadas.append(a))

    resultado = asistencia.clase_de_hoy('token')

    assert resultado == {'ok': True, 'clase': None}
    assert llamadas == []


# --- marcar ---

def test_marcar_con_codigo(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(method, url, json=None, **kwargs):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200, {'nombre': 'Ana', 'apellido': 'Garcia'})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = asistencia.marcar('token', 4, codigo='QR-123')

    assert capturado['url'].endswith('/clases/4/marcar')
    assert capturado['json'] == {'codigo': 'QR-123'}
    assert resultado['ok']


def test_marcar_codigo_manual_envia_flag(monkeypatch, respuesta_falsa):
    capturado = {}
    monkeypatch.setattr(requests, 'request',
                        lambda m, u, json=None, **k: capturado.update(json=json) or respuesta_falsa(200, {}))

    asistencia.marcar('token', 4, codigo='QR-123', manual=True)

    assert capturado['json'] == {'codigo': 'QR-123', 'manual': True}


def test_marcar_con_padron(monkeypatch, respuesta_falsa):
    capturado = {}
    monkeypatch.setattr(requests, 'request',
                        lambda m, u, json=None, **k: capturado.update(json=json) or respuesta_falsa(200, {}))

    asistencia.marcar('token', 4, padron='123456')

    assert capturado['json'] == {'padron': '123456'}


def test_marcar_codigo_tiene_prioridad_sobre_padron(monkeypatch, respuesta_falsa):
    capturado = {}
    monkeypatch.setattr(requests, 'request',
                        lambda m, u, json=None, **k: capturado.update(json=json) or respuesta_falsa(200, {}))

    asistencia.marcar('token', 4, codigo='QR-1', padron='123')

    assert capturado['json'] == {'codigo': 'QR-1'}


# --- listados ---

def test_listar_clases_usa_la_cursada_vigente(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(asistencia, 'obtener_cursada_vigente', lambda token: _cursada_vigente())
    capturado = {}

    def fake_request(method, url, **kwargs):
        capturado['url'] = url
        return respuesta_falsa(200, {'clases': [{'id': 1, 'fecha': '2026-09-01'}]})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = asistencia.listar_clases('token')

    assert capturado['url'].endswith('/cursadas/9/clases')
    assert resultado['ok'] and resultado['clases'][0]['id'] == 1


def test_listar_clases_sin_cursadas_devuelve_vacio(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(asistencia, 'obtener_cursada_vigente', lambda token: {})
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(204))

    resultado = asistencia.listar_clases('token')

    assert resultado == {'ok': True, 'clases': []}


def test_listar_asistencias_pasa_filtros_y_pagina(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(method, url, params=None, **kwargs):
        capturado['url'] = url
        capturado['params'] = params
        return respuesta_falsa(200, {'asistencias': [{'id': 1}], '_links': {'_next': '/x'}})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = asistencia.listar_asistencias('token', 4, estado='ausente', q='ana', offset=10, limit=10)

    assert capturado['url'].endswith('/clases/4/asistencias')
    assert capturado['params'] == {'_offset': 10, '_limit': 10, 'estado': 'ausente', 'q': 'ana'}
    assert resultado['asistencias'] == [{'id': 1}]
    assert resultado['links'] == {'_next': '/x'}


def test_cerrar_clase_postea_cierre(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(method, url, **kwargs):
        capturado['method'] = method
        capturado['url'] = url
        return respuesta_falsa(200, {'ausentes': 3})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = asistencia.cerrar_clase('token', 4)

    assert capturado['method'] == 'POST'
    assert capturado['url'].endswith('/clases/4/cerrar')
    assert resultado == {'ok': True, 'ausentes': 3}


# --- errores ---

def test_sin_conexion_devuelve_error(monkeypatch):
    def _sin_conexion(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, 'request', _sin_conexion)

    resultado = asistencia.enviar_qrs('token', 4)

    assert resultado['ok'] is False


def test_api_401_devuelve_unauthorized(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(401))

    resultado = asistencia.cerrar_clase('token', 4)

    assert resultado['ok'] is False
    assert resultado['unauthorized'] is True
