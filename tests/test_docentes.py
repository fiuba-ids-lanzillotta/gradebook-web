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
    ]
]


# --- service ---

def test_obtener_docente_devuelve_dict(monkeypatch, respuesta_falsa):
    capturado = {}
    monkeypatch.setattr(requests, 'get',
                        lambda url, **k: capturado.update(url=url) or respuesta_falsa(200, {'id': 7, 'nombre': 'Ana'}))

    assert docentes.obtener_docente('token', 7) == {'id': 7, 'nombre': 'Ana'}
    assert capturado['url'].endswith('/docentes/7')


def test_obtener_docente_error_devuelve_vacio(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(500))

    assert docentes.obtener_docente('token', 7) == {}


def test_listar_docentes_devuelve_lista(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(200, [{'id': 1, 'nombre': 'Ana'}]))

    assert docentes.listar_docentes('token') == [{'id': 1, 'nombre': 'Ana'}]


def test_listar_docentes_error_devuelve_vacio(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'get', lambda *a, **k: respuesta_falsa(500))

    assert docentes.listar_docentes('token') == []


def test_crear_docente_postea_campos(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_post(url, json=None, **kwargs):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(201, {'id': 5})

    monkeypatch.setattr(requests, 'post', fake_post)

    resultado = docentes.crear_docente('token', 'Ana', 'Garcia', 'a@fi.uba.ar', 'Ayudante')

    assert capturado['url'].endswith('/docentes')
    assert capturado['json'] == {'nombre': 'Ana', 'apellido': 'Garcia', 'email': 'a@fi.uba.ar', 'rol': 'Ayudante'}
    assert resultado == {'id': 5}


def test_crear_docente_error_devuelve_none(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *a, **k: respuesta_falsa(400))

    assert docentes.crear_docente('token', 'Ana', 'Garcia', 'a@fi.uba.ar', 'Ayudante') is None


def test_actualizar_docente_putea_campos(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_put(url, json=None, **kwargs):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200, {'id': 7})

    monkeypatch.setattr(requests, 'put', fake_put)

    resultado = docentes.actualizar_docente('token', 7, 'Ana', 'Garcia', 'a@fi.uba.ar', 'Profesor')

    assert capturado['url'].endswith('/docentes/7')
    assert capturado['json']['rol'] == 'Profesor'
    assert resultado == {'id': 7}


def test_eliminar_docente_true_si_200(monkeypatch, respuesta_falsa):
    capturado = {}
    monkeypatch.setattr(requests, 'delete',
                        lambda url, **k: capturado.update(url=url) or respuesta_falsa(200))

    assert docentes.eliminar_docente('token', 7) is True
    assert capturado['url'].endswith('/docentes/7')


def test_eliminar_docente_false_si_error(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'delete', lambda *a, **k: respuesta_falsa(500))

    assert docentes.eliminar_docente('token', 7) is False


def test_actualizar_permisos_envia_overrides(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_put(url, json=None, **kwargs):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200)

    monkeypatch.setattr(requests, 'put', fake_put)

    overrides = [{'permiso': 'asistencias.gestionar', 'concedido': False}]
    assert docentes.actualizar_permisos_docente('token', 7, overrides) is True
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


def test_colaborador_igual_ayudante_menos_eliminar():
    permisos_cargo = _permisos_por_cargo(CATALOGO)
    colaborador = permisos_cargo['Colaborador']

    assert 'estudiantes.eliminar' not in colaborador
    assert colaborador == [c for c in permisos_cargo['Ayudante'] if c != 'estudiantes.eliminar']


def test_body_overrides_marca_concedido_segun_codigos():
    body = _body_permisos_desde_catalogo(
        [{'codigo': 'a.leer'}, {'codigo': 'b.gestionar'}],
        {'a.leer'},
    )

    assert body == [
        {'permiso': 'a.leer', 'concedido': True},
        {'permiso': 'b.gestionar', 'concedido': False},
    ]
