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
    'aprobado_desaprobado': 'Aprobado/N.A',
    'entregado_no_entregado': 'Entregado / no entregado',
}


def etiqueta_estado(criterio: str, estado: str) -> str:
    """Sin entrega cargada, una categoría de entrega figura como no entregada."""
    if not estado and criterio == 'entregado_no_entregado':
        return ETIQUETAS_ESTADO['no_entregado']

    return ETIQUETAS_ESTADO.get(estado or '', '')


def valor_celda(criterio: str, nota, estado: str) -> str:
    if criterio == 'nota':
        return _nota_visible(nota)

    return etiqueta_estado(criterio, estado)


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
            instancia['estado_etiqueta'] = etiqueta_estado(categoria.get('criterio'), instancia.get('estado') or '')

    return categorias


def _nota_visible(valor) -> str:
    if valor is None or valor == '':
        return ''

    numero = float(valor)

    if numero == int(numero):
        return str(int(numero))

    return f'{numero:.2f}'.rstrip('0').rstrip('.')
