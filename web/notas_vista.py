"""Arma las categorías del perfil para el docente y para el alumno."""

ESTADOS = {
    'aprobado_desaprobado': (('aprobado', 'Aprobado'), ('desaprobado', 'Desaprobado')),
    'entregado_no_entregado': (('entregado', 'Entregado'), ('no_entregado', 'No entregado')),
}
ETIQUETAS_ESTADO = {
    'aprobado': 'Aprobado',
    'desaprobado': 'Desaprobado',
    'entregado': 'Entregado',
    'no_entregado': 'No entregado',
}
ETIQUETAS_CRITERIO = {
    'nota': 'Nota',
    'aprobado_desaprobado': 'Aprobado / desaprobado',
    'entregado_no_entregado': 'Entregado / no entregado',
}


def preparar_categorias(categorias: list, puede_cargar: bool) -> list:
    for categoria in categorias:
        categoria['criterio_etiqueta'] = ETIQUETAS_CRITERIO.get(categoria.get('criterio'), categoria.get('criterio'))
        categoria['opciones'] = ESTADOS.get(categoria.get('criterio'), ())
        categoria['editable'] = bool(
            puede_cargar and categoria.get('requiere_corrector')
            and (categoria.get('modalidad') != 'grupal' or categoria.get('equipo'))
        )

        for instancia in categoria.get('instancias') or []:
            instancia['nota_texto'] = _nota_visible(instancia.get('nota'))
            instancia['estado_etiqueta'] = ETIQUETAS_ESTADO.get(instancia.get('estado') or '', '')

    return categorias


def _nota_visible(valor) -> str:
    if valor is None or valor == '':
        return ''

    numero = float(valor)

    if numero == int(numero):
        return str(int(numero))

    return f'{numero:.2f}'.rstrip('0').rstrip('.')
