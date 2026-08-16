from types import SimpleNamespace

import requests

from web.services import items


# --- body_desde_formulario (función pura) ---

def test_body_desde_formulario_completo():
    form = SimpleNamespace(get=lambda clave, default=None: {
        'nombre': '  Teclado  ',
        'descripcion': '  mecánico  ',
        'activo': 'on',
    }.get(clave, default))

    assert items.body_desde_formulario(form) == {
        'nombre': 'Teclado',
        'descripcion': 'mecánico',
        'activo': True,
    }


def test_body_desde_formulario_sin_descripcion_ni_activo():
    form = SimpleNamespace(get=lambda clave, default=None: {'nombre': 'Mouse'}.get(clave, default))

    assert items.body_desde_formulario(form) == {
        'nombre': 'Mouse',
        'descripcion': None,
        'activo': False,
    }


# --- obtener_items ---

def test_obtener_items_ok(monkeypatch, respuesta_falsa, cargar_json):
    lista = cargar_json('json/items/lista.json')
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: respuesta_falsa(200, lista))

    assert items.obtener_items() == lista


def test_obtener_items_error_devuelve_vacio(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: respuesta_falsa(500))

    assert items.obtener_items() == []


def test_obtener_items_sin_conexion_devuelve_vacio(monkeypatch):
    def _sin_conexion(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, 'get', _sin_conexion)

    assert items.obtener_items() == []


# --- crear_item ---

def test_crear_item_ok(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(201))

    assert items.crear_item('tok', {'nombre': 'Teclado'}) == {'ok': True}


def test_crear_item_no_autorizado(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(401))

    resultado = items.crear_item('tok', {'nombre': 'Teclado'})

    assert resultado['ok'] is False and resultado['unauthorized'] is True


def test_crear_item_error_muestra_mensaje(monkeypatch, respuesta_falsa, cargar_json):
    error = cargar_json('json/errors/nombre_duplicado.json')
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(409, error))

    resultado = items.crear_item('tok', {'nombre': 'Teclado mecánico'})

    assert resultado['ok'] is False
    assert 'Teclado mecánico' in resultado['error']


# --- actualizar_item ---

def test_actualizar_item_ok(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'put', lambda *args, **kwargs: respuesta_falsa(200))

    assert items.actualizar_item('tok', 1, {'nombre': 'Teclado'}) == {'ok': True}


def test_actualizar_item_no_autorizado(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'put', lambda *args, **kwargs: respuesta_falsa(403))

    assert items.actualizar_item('tok', 1, {})['unauthorized'] is True


# --- eliminar_item ---

def test_eliminar_item_ok(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'delete', lambda *args, **kwargs: respuesta_falsa(204))

    assert items.eliminar_item('tok', 1) == {'ok': True}


def test_eliminar_item_error_muestra_mensaje(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(
        requests, 'delete',
        lambda *args, **kwargs: respuesta_falsa(404, {'errors': [{'message': 'no existe'}]}),
    )

    resultado = items.eliminar_item('tok', 1)

    assert resultado['ok'] is False and 'no existe' in resultado['error']
