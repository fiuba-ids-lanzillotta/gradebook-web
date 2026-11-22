import requests

from web.routes.admin.docentes import _body_permisos_desde_catalogo, _permisos_por_cargo
from web.services import docentes, permisos

CATALOGO = [
    {'codigo': codigo} for codigo in [
        'estudiantes.leer', 'estudiantes.crear', 'estudiantes.modificar',
        'estudiantes.eliminar', 'estudiantes.reactivar',
        'docentes.leer', 'docentes.gestionar',
        'asistencias.leer', 'asistencias.gestionar',
        'cursadas.leer', 'cursadas.crear', 'cursadas.modificar',
        'entregas.leer', 'permisos.asignar', 'roles.gestionar',
        'registros.leer', 'grupos.habilitar',
    ]
]


# --- service ---

def test_obtener_docente_devuelve_dict(monkeypatch, respuesta_falsa):
    capturado = {}
    monkeypatch.setattr(requests, 'request',
                        lambda metodo, url, **k: capturado.update(url=url) or respuesta_falsa(200, {'id': 7, 'nombre': 'Ana'}))

    assert docentes.obtener_docente('token', 7) == {'ok': True, 'datos': {'id': 7, 'nombre': 'Ana'}}
    assert capturado['url'].endswith('/docentes/7')


def test_obtener_docente_error_devuelve_fallo(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(500))

    resultado = docentes.obtener_docente('token', 7)

    assert resultado['ok'] is False
    assert resultado['status'] == 500


def test_listar_docentes_devuelve_lista(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(200, [{'id': 1, 'nombre': 'Ana'}]))

    assert docentes.listar_docentes('token') == {'ok': True, 'docentes': [{'id': 1, 'nombre': 'Ana'}]}


def test_listar_docentes_error_propaga_fallo(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(500))

    resultado = docentes.listar_docentes('token')

    assert resultado['ok'] is False
    assert resultado['status'] == 500


def test_crear_docente_postea_campos(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(metodo, url, json=None, **kwargs):
        capturado['metodo'] = metodo
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(201, {'id': 5})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = docentes.crear_docente('token', 'Ana', 'Garcia', 'a@fi.uba.ar', 'Ayudante')

    assert capturado['metodo'] == 'POST'
    assert capturado['url'].endswith('/docentes')
    assert capturado['json'] == {'nombre': 'Ana', 'apellido': 'Garcia', 'email': 'a@fi.uba.ar', 'rol': 'Ayudante'}
    assert resultado == {'ok': True, 'datos': {'id': 5}}


def test_crear_docente_error_propaga_fallo(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(400, {'errors': [{'message': 'email duplicado'}]}))

    resultado = docentes.crear_docente('token', 'Ana', 'Garcia', 'a@fi.uba.ar', 'Ayudante')

    assert resultado['ok'] is False
    assert 'duplicado' in resultado['error']


def test_actualizar_docente_putea_campos(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(metodo, url, json=None, **kwargs):
        capturado['metodo'] = metodo
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200, {'id': 7})

    monkeypatch.setattr(requests, 'request', fake_request)

    resultado = docentes.actualizar_docente('token', 7, 'Ana', 'Garcia', 'a@fi.uba.ar', 'Profesor')

    assert capturado['metodo'] == 'PUT'
    assert capturado['url'].endswith('/docentes/7')
    assert capturado['json']['rol'] == 'Profesor'
    assert resultado == {'ok': True, 'datos': {'id': 7}}


def test_eliminar_docente_ok_si_200(monkeypatch, respuesta_falsa):
    capturado = {}
    monkeypatch.setattr(requests, 'request',
                        lambda metodo, url, **k: capturado.update(metodo=metodo, url=url) or respuesta_falsa(200))

    assert docentes.eliminar_docente('token', 7)['ok'] is True
    assert capturado['metodo'] == 'DELETE'
    assert capturado['url'].endswith('/docentes/7')


def test_eliminar_docente_falla_si_error(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'request', lambda *a, **k: respuesta_falsa(500))

    assert docentes.eliminar_docente('token', 7)['ok'] is False


def test_actualizar_permisos_envia_overrides(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_request(metodo, url, json=None, **kwargs):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200)

    monkeypatch.setattr(requests, 'request', fake_request)

    overrides = [{'permiso': 'asistencias.gestionar', 'concedido': False}]
    assert docentes.actualizar_permisos_docente('token', 7, overrides)['ok'] is True
    assert capturado['url'].endswith('/docentes/7/permisos')
    assert capturado['json'] == {'permisos': overrides}


# --- permisos por cargo (lógica de la pantalla) ---

def test_profesor_tiene_todos_los_permisos():
    permisos_cargo = _permisos_por_cargo(CATALOGO)

    assert permisos_cargo['Profesor'] == [item['codigo'] for item in CATALOGO]


def test_ayudante_sin_permisos_de_gestion():
    ayudante = _permisos_por_cargo(CATALOGO)['Ayudante']

    assert 'estudiantes.leer' in ayudante
    assert 'asistencias.gestionar' in ayudante
    assert 'docentes.leer' in ayudante
    assert 'estudiantes.crear' not in ayudante
    assert 'estudiantes.reactivar' not in ayudante
    assert 'cursadas.crear' not in ayudante
    assert 'docentes.gestionar' not in ayudante
    assert 'permisos.asignar' not in ayudante
    assert 'roles.gestionar' not in ayudante
    assert 'grupos.habilitar' not in ayudante


def test_colaborador_igual_ayudante_menos_eliminar_y_registros():
    permisos_cargo = _permisos_por_cargo(CATALOGO)
    colaborador = permisos_cargo['Colaborador']

    assert 'estudiantes.eliminar' not in colaborador
    assert 'registros.leer' not in colaborador
    assert colaborador == [c for c in permisos_cargo['Ayudante']
                           if c not in ('estudiantes.eliminar', 'registros.leer')]


def test_body_overrides_marca_concedido_segun_codigos():
    body = _body_permisos_desde_catalogo(
        [{'codigo': 'a.leer'}, {'codigo': 'b.gestionar'}],
        {'a.leer'},
    )

    assert body == [
        {'permiso': 'a.leer', 'concedido': True},
        {'permiso': 'b.gestionar', 'concedido': False},
    ]
