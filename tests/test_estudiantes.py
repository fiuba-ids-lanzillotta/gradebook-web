from web.services.estudiantes import interpretar_busqueda


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
