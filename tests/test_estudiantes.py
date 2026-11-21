import requests

from web.services import estudiantes
from web.services.estudiantes import interpretar_busqueda, _ventana_paginas


def test_busqueda_vacia():
    assert interpretar_busqueda('   ') == {}


def test_busqueda_alfabetica_va_como_q():
    assert interpretar_busqueda('ian') == {'q': 'ian'}


def test_busqueda_numerica_va_como_q():
    assert interpretar_busqueda('116530') == {'q': '116530'}


def test_busqueda_email_va_como_q():
    assert interpretar_busqueda('ian@fi.uba.ar') == {'q': 'ian@fi.uba.ar'}


def test_busqueda_apellido_coma_nombre_es_precisa():
    assert interpretar_busqueda('Acosta, Ian') == {'apellido': 'Acosta', 'nombre': 'Ian'}


def test_listar_de_cursada_usa_anio_cuatri_de_la_vigente(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(estudiantes, 'obtener_cursada_vigente',
                        lambda token: {'anio': 2027, 'cuatrimestre': 1, 'vigente': True})
    capturado = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        capturado['params'] = params
        return respuesta_falsa(200, {'estudiantes': [], '_links': {}})

    monkeypatch.setattr(requests, 'get', fake_get)

    resultado = estudiantes.listar_de_cursada('token', q='', offset=0, limit=10)

    assert capturado['params']['anio'] == 2027 and capturado['params']['cuatrimestre'] == 1
    assert resultado['anio'] == 2027 and resultado['cuatrimestre'] == 1


def test_listar_de_cursada_respeta_anio_explicito(monkeypatch, respuesta_falsa):
    monkeypatch.setattr(estudiantes, 'obtener_cursada_vigente',
                        lambda token: {'anio': 2026, 'cuatrimestre': 2, 'vigente': True})
    capturado = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        capturado['params'] = params
        return respuesta_falsa(200, {'estudiantes': [], '_links': {}})

    monkeypatch.setattr(requests, 'get', fake_get)

    resultado = estudiantes.listar_de_cursada('token', anio=2027, cuatrimestre=1)

    assert capturado['params']['anio'] == 2027 and capturado['params']['cuatrimestre'] == 1
    assert resultado['anio'] == 2027


def test_listar_de_cursada_sin_vigente_usa_respaldo(monkeypatch, respuesta_falsa):
    from web.constants import CURSADA_ANIO, CURSADA_CUATRIMESTRE

    monkeypatch.setattr(estudiantes, 'obtener_cursada_vigente', lambda token: {})
    capturado = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        capturado['params'] = params
        return respuesta_falsa(200, {'estudiantes': [], '_links': {}})

    monkeypatch.setattr(requests, 'get', fake_get)

    resultado = estudiantes.listar_de_cursada('token')

    assert capturado['params']['anio'] == CURSADA_ANIO
    assert capturado['params']['cuatrimestre'] == CURSADA_CUATRIMESTRE
    assert resultado['anio'] == CURSADA_ANIO and resultado['cuatrimestre'] == CURSADA_CUATRIMESTRE


# --- cambio de estado ---

def test_cambiar_estado_baja_usa_endpoint_baja(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200, {'estado': 'baja'})

    monkeypatch.setattr(requests, 'post', fake_post)

    resultado = estudiantes.cambiar_estado('token', 7, 'baja', 'motivo x')

    assert capturado['url'].endswith('/estudiantes/7/baja')
    assert capturado['json'] == {'estado': 'baja', 'motivo': 'motivo x'}
    assert resultado['ok']


def test_cambiar_estado_envia_cursada_id(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        capturado['json'] = json
        return respuesta_falsa(200, {'estado': 'abandono'})

    monkeypatch.setattr(requests, 'post', fake_post)

    estudiantes.cambiar_estado('token', 7, 'abandono', cursada_id=42)

    assert capturado['json'] == {'estado': 'abandono', 'cursada_id': 42}


def test_reactivar_usa_nuevo_endpoint(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        capturado['url'] = url
        capturado['json'] = json
        return respuesta_falsa(200, {'estado': 'cursando'})

    monkeypatch.setattr(requests, 'post', fake_post)

    resultado = estudiantes.reactivar('token', 7)

    assert capturado['url'].endswith('/estudiantes/7/reactivacion')
    assert capturado['json'] == {}
    assert resultado['ok']


def test_reactivar_envia_cursada_id(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        capturado['json'] = json
        return respuesta_falsa(200, {'estado': 'cursando'})

    monkeypatch.setattr(requests, 'post', fake_post)

    estudiantes.reactivar('token', 7, cursada_id=42)

    assert capturado['json'] == {'cursada_id': 42}


def test_crear_estudiante_envia_cursada_id(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        capturado['json'] = json
        return respuesta_falsa(201, {'id': 7})

    monkeypatch.setattr(requests, 'post', fake_post)

    estudiantes.crear_estudiante(
        'token',
        {'nombre': 'Ana', 'apellido': 'Perez', 'padron': '100', 'email': 'a@fi.uba.ar'},
        cursada_id=42,
    )

    assert capturado['json']['cursada_id'] == 42
    assert capturado['json']['password'] == '100'


def test_crear_estudiante_sin_cursada_no_envia_el_campo(monkeypatch, respuesta_falsa):
    capturado = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        capturado['json'] = json
        return respuesta_falsa(201, {'id': 7})

    monkeypatch.setattr(requests, 'post', fake_post)

    estudiantes.crear_estudiante(
        'token',
        {'nombre': 'Ana', 'apellido': 'Perez', 'padron': '100', 'email': 'a@fi.uba.ar'},
    )

    assert 'cursada_id' not in capturado['json']


def test_importar_csv_envia_cursada_id_en_el_form(monkeypatch, respuesta_falsa):
    from types import SimpleNamespace

    capturado = {}

    def fake_post(url, files=None, data=None, headers=None, timeout=None):
        capturado['data'] = data
        return respuesta_falsa(201, {'inscriptos': 1})

    monkeypatch.setattr(requests, 'post', fake_post)

    archivo = SimpleNamespace(filename='alumnos.csv', stream=None, mimetype='text/csv')
    estudiantes.importar_csv('token', archivo, cursada_id=42)

    assert capturado['data'] == {'cursada_id': '42'}


# --- ventana de paginacion ---

def test_ventana_pocas_paginas_muestra_todas():
    assert _ventana_paginas(1, 5) == [1, 2, 3, 4, 5]


def test_ventana_primera_pagina():
    assert _ventana_paginas(1, 26) == [1, 2, 3, 4, '...', 26]


def test_ventana_avanza_una():
    assert _ventana_paginas(2, 26) == [2, 3, 4, 5, '...', 26]


def test_ventana_cerca_del_final_sin_elipsis():
    assert _ventana_paginas(25, 26) == [23, 24, 25, 26]


def test_ventana_sin_hueco_no_pone_elipsis():
    assert _ventana_paginas(2, 6) == [2, 3, 4, 5, 6]
