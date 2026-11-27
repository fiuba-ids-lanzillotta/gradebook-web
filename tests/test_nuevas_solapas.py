"""Services de las solapas nuevas: categorías, registros y el equipo del alumno."""
import requests

from web.services import evaluaciones, grupos, registros


def _capturar_post_o_get(monkeypatch, respuesta_falsa, status, payload):
    capturado = {}

    def fake_request(method, url, params=None, json=None, headers=None, timeout=None):
        capturado['method'] = method
        capturado['url'] = url
        capturado['params'] = params
        capturado['json'] = json
        return respuesta_falsa(status, payload)

    monkeypatch.setattr(requests, 'request', fake_request)

    return capturado


# --- evaluaciones (categorías) ---

def test_evaluaciones_listar_por_cursada(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 200, {'evaluaciones': []})

    resultado = evaluaciones.listar('token', 9)

    assert capturado['method'] == 'GET'
    assert capturado['url'].endswith('/cursadas/9/evaluaciones')
    assert resultado['ok']


def test_evaluaciones_crear_postea_body(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 201, {'id': 5})
    datos = {'nombre': 'TP1', 'tipo': 'obligatorio', 'criterio': 'nota',
             'peso': '2', 'modalidad': 'grupal', 'instancias': '1'}

    resultado = evaluaciones.crear('token', 9, datos)

    assert capturado['method'] == 'POST'
    assert capturado['url'].endswith('/cursadas/9/evaluaciones')
    assert capturado['json'] == datos
    assert resultado['ok']


def test_evaluaciones_habilitar_grupos(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 200, {'id': 5})

    evaluaciones.habilitar_grupos('token', 5, True)

    assert capturado['method'] == 'PUT'
    assert capturado['url'].endswith('/evaluaciones/5/crear-grupos')
    assert capturado['json'] == {'habilitado': True}


# --- registros (auditoría) ---

def test_registros_listar_manda_filtros(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(
        monkeypatch, respuesta_falsa, 200, {'registros': [], '_links': {}})

    registros.listar('token', email='juan', accion='grupos.crear',
                     tipo='estudiante', orden='asc', offset=8, limit=8)

    assert capturado['url'].endswith('/registros')
    assert capturado['params'] == {
        'email': 'juan',
        'accion': 'grupos.crear',
        'tipo': 'estudiante',
        '_orden': 'asc',
        '_offset': 8,
        '_limit': 8,
    }


def test_registros_listar_sin_filtros_no_manda_vacios(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(
        monkeypatch, respuesta_falsa, 200, {'registros': [], '_links': {}})

    registros.listar('token')

    assert capturado['params'] == {'_orden': 'desc', '_offset': 0, '_limit': 20}


# --- equipo del alumno (/me/equipo) ---

def test_mi_equipo_get(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 200, {'grupo': None})

    resultado = grupos.mi_equipo('token')

    assert capturado['method'] == 'GET'
    assert capturado['url'].endswith('/me/equipo')
    assert resultado['ok']


def test_crear_mi_equipo_postea_nombre_y_padrones(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 201, {'grupo': {'id': 3}})

    resultado = grupos.crear_mi_equipo('token', 'Los pibes', ['111', '222'])

    assert capturado['method'] == 'POST'
    assert capturado['url'].endswith('/me/equipo')
    assert capturado['json'] == {'nombre': 'Los pibes', 'padrones': ['111', '222']}
    assert resultado['ok']


def test_renombrar_mi_equipo_put(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 200, {})

    grupos.renombrar_mi_equipo('token', 'Otro nombre')

    assert capturado['method'] == 'PUT'
    assert capturado['url'].endswith('/me/equipo')
    assert capturado['json'] == {'nombre': 'Otro nombre'}


def test_agregar_padron_post(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 201, {})

    grupos.agregar_padron('token', '333333')

    assert capturado['method'] == 'POST'
    assert capturado['url'].endswith('/me/equipo/integrantes')
    assert capturado['json'] == {'padron': '333333'}


def test_salir_de_mi_equipo_post(monkeypatch, respuesta_falsa):
    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 200, {})

    grupos.salir_de_mi_equipo('token')

    assert capturado['method'] == 'POST'
    assert capturado['url'].endswith('/me/equipo/salir')


# --- notas (perfil del alumno) ---

def test_notas_mias_get(monkeypatch, respuesta_falsa):
    from web.services import notas

    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 200,
                                     {'estudiante': {}, 'categorias': []})

    resultado = notas.mias('token')

    assert capturado['method'] == 'GET'
    assert capturado['url'].endswith('/me/calificaciones')
    assert resultado['ok']


# --- notas_vista: preparar_categorias ---

def test_preparar_categorias_etiquetas_y_notas():
    from web.notas_vista import preparar_categorias

    categorias = preparar_categorias([
        {'nombre': 'Parcial', 'criterio': 'nota', 'modalidad': 'individual',
         'requiere_corrector': True,
         'instancias': [{'nombre': '1er parcial', 'nota': 8.0, 'estado': None},
                        {'nombre': 'Recup', 'nota': 7.25, 'estado': None}]},
        {'nombre': 'TP', 'criterio': 'aprobado_desaprobado', 'modalidad': 'grupal',
         'requiere_corrector': True, 'equipo': {'id': 9, 'nombre': 'Halcones'},
         'instancias': [{'nombre': 'Entrega', 'nota': None, 'estado': 'aprobado'}]},
    ], puede_cargar=True)

    parcial, tp = categorias
    assert parcial['criterio_etiqueta'] == 'Nota'
    assert parcial['opciones'] == ()
    assert parcial['editable'] is True
    assert [i['nota_texto'] for i in parcial['instancias']] == ['8', '7.25']

    assert tp['editable'] is True
    assert tp['opciones'] == (('aprobado', 'Aprobado'), ('desaprobado', 'Desaprobado'))
    assert tp['instancias'][0]['estado_etiqueta'] == 'Aprobado'


def test_preparar_categorias_grupal_sin_equipo_no_editable():
    from web.notas_vista import preparar_categorias

    categorias = preparar_categorias([
        {'criterio': 'nota', 'modalidad': 'grupal', 'requiere_corrector': True,
         'equipo': None, 'instancias': []},
    ], puede_cargar=True)

    assert categorias[0]['editable'] is False


def test_preparar_categorias_sin_permiso_nunca_editable():
    from web.notas_vista import preparar_categorias

    categorias = preparar_categorias([
        {'criterio': 'nota', 'modalidad': 'individual', 'requiere_corrector': True,
         'instancias': []},
    ], puede_cargar=False)

    assert categorias[0]['editable'] is False


# --- planilla de la cursada (vista) ---

def test_notas_vista_get_sin_q(monkeypatch, respuesta_falsa):
    from web.services import notas

    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 200,
                                     {'categorias': [], 'alumnos': []})

    resultado = notas.vista('token', 3)

    assert capturado['method'] == 'GET'
    assert capturado['url'].endswith('/cursadas/3/vista')
    assert capturado['params'] is None
    assert resultado['ok']


def test_notas_vista_get_con_q(monkeypatch, respuesta_falsa):
    from web.services import notas

    capturado = _capturar_post_o_get(monkeypatch, respuesta_falsa, 200, {})

    notas.vista('token', 3, q='perez')

    assert capturado['params'] == {'q': 'perez'}


def test_valor_celda_por_criterio():
    from web.notas_vista import valor_celda

    assert valor_celda('nota', 8.5, None) == '8.5'
    assert valor_celda('nota', 8.0, None) == '8'
    assert valor_celda('nota', None, None) == ''
    assert valor_celda('aprobado_desaprobado', None, 'aprobado') == 'Aprobado'
    assert valor_celda('entregado_no_entregado', None, None) == 'No entregado'
    assert valor_celda('entregado_no_entregado', None, 'entregado') == 'Entregado'
