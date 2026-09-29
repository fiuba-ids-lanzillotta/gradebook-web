import requests
import pytest

from app import app as flask_app
from web.routes.admin import docentes as rutas_docentes
from web.services import asistencia as servicio_asistencia
from web.services import cursos as servicio_cursos
from web.services import materias as servicio_materias


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True

    return flask_app.test_client()


# --- zona de estudiante (login_required; services vía requests, mockeado) ---

def _sesion_estudiante(client):
    """Simula un estudiante logueado (la zona del sitio exige sesión)."""
    with client.session_transaction() as sesion:
        sesion['token'] = 'token-estudiante'
        sesion['usuario'] = {'id': 1, 'tipo': 'estudiante', 'email': 'a@fi.uba.ar', 'rol': 'usuario'}


def _sesion_docente_superadmin(client):
    """Simula un docente superadmin logueado (tiene todos los permisos)."""
    with client.session_transaction() as sesion:
        sesion['token'] = 'token-docente'
        sesion['usuario'] = {
            'id': 1,
            'tipo': 'docente',
            'email': 'p@fi.uba.ar',
            'rol': 'super_admin',
            'permisos': [
                'estudiantes.leer',
                'estudiantes.crear',
                'estudiantes.modificar',
                'estudiantes.eliminar',
                'estudiantes.reactivar',
                'docentes.leer',
                'docentes.gestionar',
                'asistencias.leer',
                'asistencias.gestionar',
            ],
        }


def _sesion_docente(client, permisos=()):
    """Simula un docente logueado con permisos puntuales."""
    with client.session_transaction() as sesion:
        sesion['token'] = 'token-docente'
        sesion['nombre_completo'] = 'Profesor Test'
        sesion['usuario'] = {
            'id': 1,
            'tipo': 'docente',
            'email': 'p@fi.uba.ar',
            'rol': 'profesor',
            'permisos': list(permisos),
        }


def test_pagina_inicio_sin_sesion_redirige_a_login(client):
    respuesta = client.get('/')

    assert respuesta.status_code == 302
    assert '/admin/login' in respuesta.headers['Location']


def test_pagina_inicio_ok(client):
    _sesion_estudiante(client)

    respuesta = client.get('/')

    assert respuesta.status_code == 200


def test_pagina_items_ok(client, monkeypatch, respuesta_falsa, cargar_json):
    _sesion_estudiante(client)
    lista = cargar_json('json/items/lista.json')
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: respuesta_falsa(200, lista))

    respuesta = client.get('/items')

    assert respuesta.status_code == 200


def test_pagina_items_degrada_si_api_cae(client, monkeypatch):
    _sesion_estudiante(client)

    def _sin_conexion(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, 'get', _sin_conexion)

    respuesta = client.get('/items')

    assert respuesta.status_code == 200


def test_pagina_inexistente_devuelve_404(client):
    respuesta = client.get('/no-existe')

    assert respuesta.status_code == 404


# --- admin (protegido por admin_required) ---

def test_admin_panel_requiere_login(client):
    respuesta = client.get('/admin/')

    assert respuesta.status_code == 302
    assert '/admin/login' in respuesta.headers['Location']


def test_admin_items_requiere_login(client):
    respuesta = client.get('/admin/items')

    assert respuesta.status_code == 302
    assert '/admin/login' in respuesta.headers['Location']


def test_login_exitoso_redirige_al_panel(client, monkeypatch, respuesta_falsa, cargar_json):
    cuerpo = cargar_json('json/auth/login.json')
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(200, cuerpo))

    respuesta = client.post('/admin/login', data={'usuario': 'admin', 'password': 'secreto'})

    assert respuesta.status_code == 302
    assert respuesta.headers['Location'].endswith('/admin/')


def test_login_fallido_muestra_pagina(client, monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(401))

    respuesta = client.post('/admin/login', data={'usuario': 'admin', 'password': 'mala'})

    assert respuesta.status_code == 200


# --- recuperación de contraseña (rutas) ---

def test_recuperar_get_ok(client):
    respuesta = client.get('/admin/recuperar')

    assert respuesta.status_code == 200


def test_recuperar_post_muestra_mensaje_uniforme(client, monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(200, {'mensaje': 'ok'}))

    respuesta = client.post('/admin/recuperar', data={'email': 'a@fi.uba.ar'})

    assert respuesta.status_code == 200


def test_cambiar_contrasena_sin_token_muestra_error(client):
    respuesta = client.get('/admin/cambiar-contrasena')

    assert respuesta.status_code == 200
    assert 'enlace' in respuesta.get_data(as_text=True).lower()


def test_cambiar_contrasena_post_ok(client, monkeypatch, respuesta_falsa):
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(200, {'mensaje': 'ok'}))

    respuesta = client.post('/admin/cambiar-contrasena',
                            data={'token': 't', 'password': 'nuevaClave1', 'password_confirm': 'nuevaClave1'})

    assert respuesta.status_code == 200


def test_cambiar_contrasena_passwords_no_coinciden(client):
    respuesta = client.post('/admin/cambiar-contrasena',
                            data={'token': 't', 'password': 'a', 'password_confirm': 'b'})

    assert respuesta.status_code == 200
    assert 'coinciden' in respuesta.get_data(as_text=True).lower()


# --- panel: baja / reactivación ---

def test_dar_de_alta_usa_endpoint_reactivacion(client, monkeypatch, respuesta_falsa):
    _sesion_docente_superadmin(client)
    capturado = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        capturado['url'] = url
        return respuesta_falsa(200, {'estado': 'cursando'})

    monkeypatch.setattr(requests, 'post', fake_post)

    respuesta = client.post('/admin/alumnos/7/alta')

    assert respuesta.status_code == 302
    assert '/admin/' in respuesta.headers['Location']
    assert capturado['url'].endswith('/estudiantes/7/reactivacion')


def test_login_estudiante_redirige_al_sitio(client, monkeypatch, respuesta_falsa, cargar_json):
    cuerpo = cargar_json('json/auth/login_estudiante.json')
    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: respuesta_falsa(200, cuerpo))
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: respuesta_falsa(200, cuerpo['usuario']))

    respuesta = client.post('/admin/login', data={'email': 'a@fi.uba.ar', 'password': 'x'})

    assert respuesta.status_code == 302
    assert '/admin/' not in respuesta.headers['Location']


# --- panel: permisos y listado ---

def test_admin_sin_permiso_redirige_a_primera_solapa(client):
    _sesion_docente(client, ['asistencias.leer'])

    respuesta = client.get('/admin/')

    assert respuesta.status_code == 302
    assert respuesta.headers['Location'].endswith('/admin/asistencia')


def test_admin_sin_ningun_permiso_muestra_error(client):
    _sesion_docente(client)

    respuesta = client.get('/admin/')

    assert respuesta.status_code == 200
    assert 'permiso' in respuesta.get_data(as_text=True).lower()


def test_admin_panel_lista_alumnos(client, monkeypatch, respuesta_falsa):
    _sesion_docente(client, ['estudiantes.leer'])

    def fake_get(url, params=None, **kwargs):
        if url.endswith('/cursadas'):
            return respuesta_falsa(200, {'cursadas': [{'id': 1, 'anio': 2026, 'cuatrimestre': 2, 'vigente': True}]})

        return respuesta_falsa(200, {
            'estudiantes': [
                {'id': 1, 'nombre': 'Ana', 'apellido': 'Garcia', 'padron': '123', 'email': 'a@fi.uba.ar', 'estado': 'cursando'},
            ],
            '_links': {},
        })

    monkeypatch.setattr(requests, 'get', fake_get)

    respuesta = client.get('/admin/')

    assert respuesta.status_code == 200
    assert 'Garcia' in respuesta.get_data(as_text=True)


# --- panel: mutaciones de alumnos ---

def test_agregar_alumno_postea_y_redirige_a_busqueda(client, monkeypatch, respuesta_falsa):
    _sesion_docente(client, ['estudiantes.leer', 'estudiantes.crear'])
    capturado = {}

    def fake_post(url, json=None, **kwargs):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(201, {'id': 9})

    monkeypatch.setattr(requests, 'post', fake_post)

    respuesta = client.post('/admin/alumnos', data={
        'nombre': 'Ana', 'apellido': 'Garcia', 'padron': '123456', 'email': 'a@fi.uba.ar',
    })

    assert respuesta.status_code == 302
    assert 'q=123456' in respuesta.headers['Location']
    assert capturado['url'].endswith('/estudiantes')
    assert capturado['json']['password'] == '123456'


def test_editar_alumno_putea_cambios(client, monkeypatch, respuesta_falsa):
    _sesion_docente(client, ['estudiantes.leer', 'estudiantes.modificar'])
    capturado = {}

    def fake_put(url, json=None, **kwargs):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200, {})

    monkeypatch.setattr(requests, 'put', fake_put)

    respuesta = client.post('/admin/alumnos/7/editar', data={
        'nombre': 'Ana', 'apellido': 'Garcia', 'padron': '123', 'email': 'a@fi.uba.ar',
    })

    assert respuesta.status_code == 302
    assert capturado['url'].endswith('/estudiantes/7')
    assert capturado['json']['apellido'] == 'Garcia'


def test_abandonar_postea_estado_abandono(client, monkeypatch, respuesta_falsa):
    _sesion_docente(client, ['estudiantes.leer'])
    capturado = {}

    def fake_post(url, json=None, **kwargs):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200, {})

    monkeypatch.setattr(requests, 'post', fake_post)

    respuesta = client.post('/admin/alumnos/7/abandonar')

    assert respuesta.status_code == 302
    assert capturado['url'].endswith('/estudiantes/7/baja')
    assert capturado['json'] == {'estado': 'abandono'}


def test_baja_sin_motivo_no_llama_api(client, monkeypatch, respuesta_falsa):
    _sesion_docente(client, ['estudiantes.leer'])
    llamadas = []

    def fake_post(*args, **kwargs):
        llamadas.append(args)
        return respuesta_falsa(500)

    monkeypatch.setattr(requests, 'post', fake_post)

    respuesta = client.post('/admin/alumnos/7/baja')

    assert respuesta.status_code == 302
    assert llamadas == []


def test_baja_con_motivo_postea_estado(client, monkeypatch, respuesta_falsa):
    _sesion_docente(client, ['estudiantes.leer'])
    capturado = {}

    def fake_post(url, json=None, **kwargs):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200, {})

    monkeypatch.setattr(requests, 'post', fake_post)

    respuesta = client.post('/admin/alumnos/7/baja', data={'motivo': 'no rinde'})

    assert respuesta.status_code == 302
    assert capturado['url'].endswith('/estudiantes/7/baja')
    assert capturado['json'] == {'estado': 'baja', 'motivo': 'no rinde'}


def test_descargar_csv_devuelve_archivo(client, monkeypatch, respuesta_falsa):
    _sesion_docente(client, ['estudiantes.leer'])

    def fake_get(url, params=None, **kwargs):
        if url.endswith('/estudiantes/csv'):
            return respuesta_falsa(200, content=b'Legajo;Alumno\n123;Ana\n',
                                   headers={'Content-Type': 'text/csv'})

        return respuesta_falsa(200, {'estudiantes': []})

    monkeypatch.setattr(requests, 'get', fake_get)

    respuesta = client.get('/admin/alumnos/csv')

    assert respuesta.status_code == 200
    assert 'attachment' in respuesta.headers.get('Content-Disposition', '')
    assert 'Legajo' in respuesta.get_data(as_text=True)


def test_subir_csv_sin_archivo_redirige(client):
    _sesion_docente(client, ['estudiantes.crear'])

    respuesta = client.post('/admin/alumnos/csv')

    assert respuesta.status_code == 302
    assert respuesta.headers['Location'].endswith('/admin/')


# --- asistencia (rutas) ---

def test_asistencia_requiere_login(client):
    respuesta = client.get('/admin/asistencia')

    assert respuesta.status_code == 302
    assert '/admin/login' in respuesta.headers['Location']


def test_asistencia_sin_permiso_redirige(client):
    _sesion_docente(client, ['estudiantes.leer'])

    respuesta = client.get('/admin/asistencia')

    assert respuesta.status_code == 302
    assert '/admin/asistencia' not in respuesta.headers['Location']


def test_asistencia_index_ok(client, monkeypatch):
    _sesion_docente(client, ['asistencias.leer'])
    monkeypatch.setattr(servicio_asistencia, 'clase_de_hoy', lambda token: {'ok': True, 'clase': None})

    respuesta = client.get('/admin/asistencia')

    assert respuesta.status_code == 200


def test_crear_clase_sin_permiso_devuelve_403(client):
    _sesion_docente(client, ['asistencias.leer'])

    respuesta = client.post('/admin/asistencia/clases')

    assert respuesta.status_code == 403
    assert respuesta.get_json()['ok'] is False


def test_crear_clase_responde_json(client, monkeypatch):
    _sesion_docente(client, ['asistencias.gestionar'])
    monkeypatch.setattr(servicio_asistencia, 'crear_clase_hoy',
                        lambda token: {'ok': True, 'clase': {'id': 4}, 'clase_id': 4, 'total_estudiantes': 10, 'generados': 10})

    respuesta = client.post('/admin/asistencia/clases')

    assert respuesta.status_code == 200
    assert respuesta.get_json()['ok'] is True
    assert respuesta.get_json()['clase']['id'] == 4


def test_crear_clase_error_api_propaga(client, monkeypatch):
    _sesion_docente(client, ['asistencias.gestionar'])
    monkeypatch.setattr(servicio_asistencia, 'crear_clase_hoy',
                        lambda token: {'ok': False, 'error': 'sin cursada'})

    respuesta = client.post('/admin/asistencia/clases')

    assert respuesta.status_code == 400
    assert respuesta.get_json()['error'] == 'sin cursada'


def test_marcar_asistencia_por_codigo(client, monkeypatch):
    _sesion_docente(client, ['asistencias.gestionar'])
    capturado = {}

    def fake_marcar(token, clase_id, codigo='', padron='', manual=False):
        capturado.update(clase_id=clase_id, codigo=codigo, manual=manual)
        return {'ok': True, 'nombre': 'Ana', 'apellido': 'Garcia', 'padron': '123'}

    monkeypatch.setattr(servicio_asistencia, 'marcar', fake_marcar)

    respuesta = client.post('/admin/asistencia/clases/4/marcar', json={'codigo': 'QR-1'})

    assert respuesta.status_code == 200
    assert capturado == {'clase_id': 4, 'codigo': 'QR-1', 'manual': False}
    assert 'Ana' in respuesta.get_json()['mensaje']


def test_marcar_sin_codigo_ni_padron_400(client):
    _sesion_docente(client, ['asistencias.gestionar'])

    respuesta = client.post('/admin/asistencia/clases/4/marcar', json={})

    assert respuesta.status_code == 400


def test_marcar_con_ambos_codigo_y_padron_400(client):
    _sesion_docente(client, ['asistencias.gestionar'])

    respuesta = client.post('/admin/asistencia/clases/4/marcar',
                            json={'codigo': 'QR-1', 'padron': '123'})

    assert respuesta.status_code == 400


def test_marcar_padron_no_numerico_400(client):
    _sesion_docente(client, ['asistencias.gestionar'])

    respuesta = client.post('/admin/asistencia/clases/4/marcar', json={'padron': 'abc'})

    assert respuesta.status_code == 400


def test_cerrar_clase_redirige_al_listado(client, monkeypatch):
    _sesion_docente(client, ['asistencias.gestionar'])
    monkeypatch.setattr(servicio_asistencia, 'cerrar_clase',
                        lambda token, clase_id: {'ok': True, 'ausentes': 3})

    respuesta = client.post('/admin/asistencia/clases/4/cerrar')

    assert respuesta.status_code == 302
    assert 'clase_id=4' in respuesta.headers['Location']


def test_cerrar_clase_sin_permiso_no_llama_api(client, monkeypatch):
    _sesion_docente(client, ['asistencias.leer'])
    llamadas = []
    monkeypatch.setattr(servicio_asistencia, 'cerrar_clase', lambda *a, **k: llamadas.append(a))

    respuesta = client.post('/admin/asistencia/clases/4/cerrar')

    assert respuesta.status_code == 302
    assert llamadas == []


def test_listado_asistencia_renderiza(client, monkeypatch):
    _sesion_docente(client, ['asistencias.leer'])
    monkeypatch.setattr(servicio_asistencia, 'listar_clases',
                        lambda token: {'ok': True, 'clases': [{'id': 4, 'fecha': '2026-09-01', 'titulo': 'Clase 1'}]})
    monkeypatch.setattr(servicio_asistencia, 'listar_asistencias',
                        lambda token, clase_id, **kw: {'ok': True, 'asistencias': [], 'links': {}, 'offset': 0, 'limit': 10})

    respuesta = client.get('/admin/asistencia/listado')

    assert respuesta.status_code == 200


# --- docentes (rutas) ---

def test_docentes_requiere_permiso_lectura(client):
    _sesion_docente(client, ['estudiantes.leer'])

    respuesta = client.get('/admin/docentes')

    assert respuesta.status_code == 302
    assert '/admin/docentes' not in respuesta.headers['Location']


def test_docentes_lista_ok(client, monkeypatch):
    _sesion_docente(client, ['docentes.leer'])
    monkeypatch.setattr(rutas_docentes, 'listar_docentes',
                        lambda token: [{'id': 1, 'nombre': 'Ana', 'apellido': 'Garcia', 'rol': 'Ayudante', 'email': 'a@fi.uba.ar'}])
    monkeypatch.setattr(rutas_docentes, 'obtener_catalogo_permisos', lambda token: [])

    respuesta = client.get('/admin/docentes')

    assert respuesta.status_code == 200


def test_crear_docente_campos_incompletos_no_llama_api(client, monkeypatch):
    _sesion_docente(client, ['docentes.gestionar'])
    llamadas = []
    monkeypatch.setattr(rutas_docentes, 'crear_docente', lambda *a, **k: llamadas.append(a))

    respuesta = client.post('/admin/docentes', data={'nombre': 'Ana'})

    assert respuesta.status_code == 302
    assert llamadas == []


def test_crear_docente_ok_asigna_permisos_por_rol(client, monkeypatch):
    _sesion_docente(client, ['docentes.gestionar', 'permisos.asignar'])
    capturado = {}
    catalogo = [{'codigo': 'estudiantes.leer'}, {'codigo': 'docentes.gestionar'}]

    monkeypatch.setattr(rutas_docentes, 'crear_docente',
                        lambda token, nombre, apellido, email, rol: {'id': 5})
    monkeypatch.setattr(rutas_docentes, 'obtener_catalogo_permisos', lambda token: catalogo)
    monkeypatch.setattr(rutas_docentes, 'actualizar_permisos_docente',
                        lambda token, docente_id, permisos: capturado.update(docente_id=docente_id, permisos=permisos) or True)

    respuesta = client.post('/admin/docentes', data={
        'nombre': 'Ana', 'apellido': 'Garcia', 'email': 'a@fi.uba.ar', 'rol': 'Ayudante',
    })

    assert respuesta.status_code == 302
    assert capturado['docente_id'] == 5
    assert capturado['permisos'] == [
        {'permiso': 'estudiantes.leer', 'concedido': True},
        {'permiso': 'docentes.gestionar', 'concedido': False},
    ]


def test_desactivar_profesor_no_llama_api(client, monkeypatch):
    _sesion_docente(client, ['docentes.gestionar'])
    monkeypatch.setattr(rutas_docentes, 'listar_docentes',
                        lambda token: [{'id': 7, 'nombre': 'Ana', 'apellido': 'Garcia', 'rol': 'Profesor'}])
    llamadas = []
    monkeypatch.setattr(rutas_docentes, 'eliminar_docente', lambda *a, **k: llamadas.append(a))

    respuesta = client.post('/admin/docentes/7/desactivar')

    assert respuesta.status_code == 302
    assert llamadas == []


def test_desactivar_ayudante_llama_eliminar(client, monkeypatch):
    _sesion_docente(client, ['docentes.gestionar'])
    capturado = {}
    monkeypatch.setattr(rutas_docentes, 'listar_docentes',
                        lambda token: [{'id': 7, 'nombre': 'Ana', 'apellido': 'Garcia', 'rol': 'Ayudante'}])
    monkeypatch.setattr(rutas_docentes, 'eliminar_docente',
                        lambda token, docente_id: capturado.update(docente_id=docente_id) or True)

    respuesta = client.post('/admin/docentes/7/desactivar')

    assert respuesta.status_code == 302
    assert capturado['docente_id'] == 7


# --- cursadas (rutas) ---

def test_cursadas_requiere_login(client):
    respuesta = client.get('/admin/cursadas')

    assert respuesta.status_code == 302
    assert '/admin/login' in respuesta.headers['Location']


def test_cursadas_sin_permiso_redirige(client):
    _sesion_docente(client, ['estudiantes.leer'])

    respuesta = client.get('/admin/cursadas')

    assert respuesta.status_code == 302
    assert '/admin/cursadas' not in respuesta.headers['Location']


def test_cursadas_index_ok(client, monkeypatch):
    _sesion_docente(client, ['cursadas.leer'])
    monkeypatch.setattr(servicio_cursos, 'listar_cursadas', lambda token: {
        'ok': True,
        'cursadas': [
            {'id': 9, 'codigo': 'TB022', 'nombre': 'IDS', 'anio': 2026, 'cuatrimestre': 2,
             'fecha_inicio': '2026-08-01', 'fecha_fin': '2026-12-15', 'vigente': True},
            {'id': 5, 'codigo': 'TB022', 'nombre': 'IDS', 'anio': 2026, 'cuatrimestre': 1,
             'fecha_inicio': '2026-03-01', 'fecha_fin': '2026-07-15', 'vigente': False},
        ],
    })
    monkeypatch.setattr(servicio_materias, 'listar_materias', lambda token: [
        {'id': 1, 'codigo': 'TB022', 'nombre': 'IDS'},
        {'id': 2, 'codigo': 'TB099', 'nombre': 'Materia sin cursada'},
    ])

    respuesta = client.get('/admin/cursadas')

    assert respuesta.status_code == 200
    assert 'Cuatrimestre actual' in respuesta.get_data(as_text=True)
    assert '2C 2026' in respuesta.get_data(as_text=True)
    # El datalist sale del catálogo real, no solo de materias con cursada
    assert 'TB099' in respuesta.get_data(as_text=True)


def test_cursadas_index_sin_catalogo_usa_cursadas(client, monkeypatch):
    _sesion_docente(client, ['cursadas.leer'])
    monkeypatch.setattr(servicio_cursos, 'listar_cursadas', lambda token: {
        'ok': True,
        'cursadas': [
            {'id': 9, 'codigo': 'TB022', 'nombre': 'IDS', 'anio': 2026, 'cuatrimestre': 2,
             'fecha_inicio': '2026-08-01', 'fecha_fin': '2026-12-15', 'vigente': True},
        ],
    })
    monkeypatch.setattr(servicio_materias, 'listar_materias', lambda token: [])

    respuesta = client.get('/admin/cursadas')

    assert respuesta.status_code == 200
    assert 'TB022' in respuesta.get_data(as_text=True)


def test_cursadas_index_sin_vigente(client, monkeypatch):
    _sesion_docente(client, ['cursadas.leer'])
    monkeypatch.setattr(servicio_cursos, 'listar_cursadas', lambda token: {'ok': True, 'cursadas': []})
    monkeypatch.setattr(servicio_materias, 'listar_materias', lambda token: [])

    respuesta = client.get('/admin/cursadas')

    assert respuesta.status_code == 200
    assert 'No hay cursada vigente' in respuesta.get_data(as_text=True)


def test_crear_cursada_postea_a_api(client, monkeypatch, respuesta_falsa):
    _sesion_docente(client, ['cursadas.leer', 'cursadas.crear'])
    capturado = {}

    def fake_request(method, url, json=None, **kwargs):
        capturado['method'] = method
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(201, {'id': 9})

    monkeypatch.setattr(requests, 'request', fake_request)

    respuesta = client.post('/admin/cursadas', data={
        'codigo': 'tb022', 'nombre': 'IDS', 'anio': '2027', 'cuatrimestre': '1',
        'fecha_inicio': '2027-03-01', 'fecha_fin': '2027-07-15',
    })

    assert respuesta.status_code == 302
    assert capturado['url'].endswith('/cursadas')
    assert capturado['json']['codigo'] == 'TB022'


def test_crear_cursada_sin_permiso_no_llama_api(client, monkeypatch):
    _sesion_docente(client, ['cursadas.leer'])
    llamadas = []
    monkeypatch.setattr(requests, 'request', lambda *a, **k: llamadas.append(a))

    respuesta = client.post('/admin/cursadas', data={'codigo': 'TB022'})

    assert respuesta.status_code == 302
    assert llamadas == []


def test_editar_cursada_putea_a_api(client, monkeypatch, respuesta_falsa):
    _sesion_docente(client, ['cursadas.leer', 'cursadas.modificar'])
    capturado = {}

    def fake_request(method, url, json=None, **kwargs):
        capturado['method'] = method
        capturado['url'] = url
        return respuesta_falsa(200, {'id': 9})

    monkeypatch.setattr(requests, 'request', fake_request)

    respuesta = client.post('/admin/cursadas/9', data={
        'codigo': 'TB022', 'nombre': 'IDS', 'anio': '2026', 'cuatrimestre': '2',
        'fecha_inicio': '2026-08-01', 'fecha_fin': '2026-12-10',
    })

    assert respuesta.status_code == 302
    assert capturado['method'] == 'PUT'
    assert capturado['url'].endswith('/cursadas/9')


def test_editar_cursada_sin_permiso_no_llama_api(client, monkeypatch):
    _sesion_docente(client, ['cursadas.leer'])
    llamadas = []
    monkeypatch.setattr(requests, 'request', lambda *a, **k: llamadas.append(a))

    respuesta = client.post('/admin/cursadas/9', data={'codigo': 'TB022'})

    assert respuesta.status_code == 302
    assert llamadas == []
