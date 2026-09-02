"""Pantalla admin: tomar asistencia de hoy y marcar presente (QR / código / padrón)."""
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash

from web.auth_sesion import admin_required, redirigir_a_login_sin_sesion
from web.routes.admin.panel import _token, contexto_admin
from web.services import asistencia as servicio
from web.services.estudiantes import paginas_desde_links

asistencia_bp = Blueprint('asistencia', __name__)

ESTADO_ETIQUETA = {
    'presente': 'Presente',
    'pendiente': 'Pendiente',
    'ausente': 'Ausente',
}

METODO_ETIQUETA = {
    'qr': 'QR',
    'manual': 'Código',
    'padron': 'Padrón',
}

ESTADOS_FILTRO = ('presente', 'pendiente', 'ausente')


def _quiere_json() -> bool:
    acepta = request.headers.get('Accept') or ''

    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in acepta
    )


def _json_o_error(resultado, status_ok=200):
    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if not resultado.get('ok'):
        codigo = resultado.get('status') or 400

        if codigo < 400:
            codigo = 400
        return jsonify({'ok': False, 'error': resultado.get('error') or 'No se pudo completar.'}), codigo

    return jsonify({'ok': True, **{k: v for k, v in resultado.items() if k != 'ok'}}), status_ok


@asistencia_bp.route('/asistencia')
@admin_required
def index():
    clase_hoy = servicio.clase_de_hoy(_token())

    if clase_hoy.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    clase = (clase_hoy.get('clase') or {}) if clase_hoy.get('ok') else {}

    return render_template(
        'admin/asistencia.html',
        clase_id=clase.get('id') or '',
        fecha=servicio.fecha_hoy(),
        **contexto_admin('asistencia'),
    )


@asistencia_bp.route('/asistencia/clases', methods=['POST'])
@admin_required
def crear_clase():
    return _json_o_error(servicio.crear_clase_hoy(_token()), status_ok=200)


@asistencia_bp.route('/asistencia/clases/<int:clase_id>/enviar-qrs', methods=['POST'])
@admin_required
def enviar_qrs(clase_id):
    return _json_o_error(servicio.enviar_qrs(_token(), clase_id))


@asistencia_bp.route('/asistencia/clases/<int:clase_id>/envio', methods=['GET'])
@admin_required
def estado_envio(clase_id):
    return _json_o_error(servicio.estado_envio(_token(), clase_id))


@asistencia_bp.route('/asistencia/clases/<int:clase_id>/marcar', methods=['POST'])
@admin_required
def marcar(clase_id):
    cuerpo = request.get_json(silent=True) or {}
    codigo = (request.form.get('codigo') or cuerpo.get('codigo') or '').strip()
    padron = (request.form.get('padron') or cuerpo.get('padron') or '').strip()
    manual = bool(cuerpo.get('manual')) or request.form.get('manual') == 'true'

    if padron and not padron.isdigit():
        error = 'El padrón debe ser un número.'

        if _quiere_json():
            return jsonify({'ok': False, 'error': error}), 400

        return jsonify({'ok': False, 'error': error}), 400

    if bool(codigo) == bool(padron):
        error = 'Ingresá el código del QR o el padrón, no los dos.'

        return jsonify({'ok': False, 'error': error}), 400

    resultado = servicio.marcar(_token(), clase_id, codigo=codigo, padron=padron, manual=manual)
    
    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if not resultado.get('ok'):
        codigo_http = resultado.get('status') or 400

        if codigo_http < 400:
            codigo_http = 400

        return jsonify({'ok': False, 'error': resultado.get('error') or 'No se pudo marcar.'}), codigo_http

    nombre = f"{resultado.get('apellido') or ''} {resultado.get('nombre') or ''}".strip()
    padron_ok = resultado.get('padron') or padron
    mensaje = f'Presente: {nombre}' + (f' ({padron_ok})' if padron_ok else '')
    
    return jsonify({
        'ok': True,
        'mensaje': mensaje,
        'padron': padron_ok,
        'nombre': resultado.get('nombre'),
        'apellido': resultado.get('apellido'),
        'metodo': resultado.get('metodo'),
        'estado': resultado.get('estado'),
    })




@asistencia_bp.route('/asistencia/listado')
@admin_required
def listado():
    token = _token()
    clases_res = servicio.listar_clases(token)

    if clases_res.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    clases = clases_res.get('clases') or [] if clases_res.get('ok') else []

    for clase in clases:
        clase['etiqueta'] = servicio.etiqueta_clase(clase)

    pedida = (request.args.get('clase_id') or '').strip()
    estado = (request.args.get('estado') or '').strip()
    q = (request.args.get('q') or '').strip()

    try:
        offset = max(int(request.args.get('_offset', 0)), 0)
    except (TypeError, ValueError):
        offset = 0

    try:
        limit = max(int(request.args.get('_limit', 10)), 1)
    except (TypeError, ValueError):
        limit = 10
    
    if estado not in ESTADOS_FILTRO:
        estado = ''

    clase = None

    if pedida.isdigit():
        clase = next((fila for fila in clases if str(fila.get('id')) == pedida), None)

    if clase is None and clases:
        clase = clases[0]

    asistencias = []
    error = None if clases_res.get('ok') else (clases_res.get('error') or 'No se pudieron cargar las clases.')

    paginacion = {'actual': 1, 'total': 1, 'numeros': [1], 'offset': offset, 'limit': limit}

    if clase and clase.get('id'):
        lista = servicio.listar_asistencias(
            token, int(clase['id']), estado=estado, q=q, offset=offset, limit=limit
        )

        if lista.get('unauthorized'):
            return redirigir_a_login_sin_sesion()

        if lista.get('ok'):
            asistencias = lista.get('asistencias') or []
            paginacion = paginas_desde_links(
                lista.get('links') or {},
                lista.get('offset', offset),
                lista.get('limit', limit),
            )
        else:
            error = lista.get('error') or 'No se pudo cargar el listado de esa clase.'
    resumen = {
        'presente': sum(1 for fila in asistencias if fila.get('estado') == 'presente'),
        'pendiente': sum(1 for fila in asistencias if fila.get('estado') == 'pendiente'),
        'ausente': sum(1 for fila in asistencias if fila.get('estado') == 'ausente'),
        'total': len(asistencias),
    }

    return render_template(
        'admin/asistencia_listado.html',
        clases=clases,
        clase=clase,
        asistencias=asistencias,
        resumen=resumen,
        error=error,
        estado_filtro=estado,
        q=q,
        estado_etiqueta=ESTADO_ETIQUETA,
        metodo_etiqueta=METODO_ETIQUETA,
        paginacion=paginacion,
        **contexto_admin('asistencia'),
    )


@asistencia_bp.route('/asistencia/clases/<int:clase_id>/cerrar', methods=['POST'])
@admin_required
def cerrar(clase_id):
    resultado = servicio.cerrar_clase(_token(), clase_id)

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if resultado.get('ok'):
        flash('Se cerró la toma. Los pendientes pasaron a ausentes.', 'ok')
    else:
        flash(resultado.get('error') or 'No se pudo cerrar la clase.', 'error')

    return redirect(url_for('web.admin.asistencia.listado', clase_id=clase_id))