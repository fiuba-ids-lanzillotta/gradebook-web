from web.services import respuestas_api


def test_respuesta_no_autorizada(respuesta_falsa):
    assert respuestas_api.respuesta_no_autorizada(respuesta_falsa(401))['unauthorized'] is True
    assert respuestas_api.respuesta_no_autorizada(respuesta_falsa(403))['unauthorized'] is True
    assert respuestas_api.respuesta_no_autorizada(respuesta_falsa(200)) is None


def test_mensaje_error_api_extrae_descripcion(respuesta_falsa):
    con_errores = respuesta_falsa(400, {'errors': [{'description': 'nombre inválido'}]})

    assert respuestas_api.mensaje_error_api(con_errores) == 'nombre inválido'


def test_mensaje_error_api_generico_sin_cuerpo(respuesta_falsa):
    assert respuestas_api.mensaje_error_api(respuesta_falsa(500)) == 'Error del servidor (HTTP 500).'
