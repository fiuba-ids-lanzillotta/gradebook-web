"""Pantalla admin para tomar asistencia (escáner visual + aviso por mail)."""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from web.auth_sesion import admin_required, redirigir_a_login_sin_sesion
from web.routes.admin.panel import _token, contexto_admin
from web.services import asistencia as servicio

asistencia_bp = Blueprint('asistencia', __name__)


def _quiere_json() -> bool:
    acepta = request.headers.get('Accept') or ''
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in acepta
    )


@asistencia_bp.route('/asistencia')
@admin_required
def index():
    return render_template(
        'admin/asistencia.html',
        **contexto_admin('asistencia'),
    )


@asistencia_bp.route('/asistencia/tomar', methods=['POST'])
@admin_required
def tomar():
    resultado = servicio.notificar_toma_asistencia(_token())
    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
    if resultado.get('ok'):
        extra = ' (simulado: no hay SMTP configurado)' if resultado.get('simulado') else ''
        flash(
            f"Mails de aviso: {resultado.get('enviados', 0)}. "
            f"Omitidos: {resultado.get('omitidos', 0)}. "
            f"Errores: {resultado.get('errores', 0)}.{extra}",
            'ok',
        )
    else:
        flash(resultado.get('error') or 'No se pudo avisar a los alumnos.', 'error')
    return redirect(url_for('web.admin.asistencia.index'))


@asistencia_bp.route('/asistencia/marcar', methods=['POST'])
@admin_required
def marcar():
    """Solo visual: no hay backend de presentes todavía."""
    codigo = (request.form.get('codigo') or (request.get_json(silent=True) or {}).get('codigo') or '').strip()
    padron = (request.form.get('padron') or (request.get_json(silent=True) or {}).get('padron') or '').strip()
    if padron and not padron.isdigit():
        error = 'El padrón debe ser un número.'
        if _quiere_json():
            return jsonify({'ok': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('web.admin.asistencia.index'))
    if not codigo and not padron:
        error = 'Ingresá el código del QR o el padrón.'
        if _quiere_json():
            return jsonify({'ok': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('web.admin.asistencia.index'))

    mensaje = (
        f'Leído{" padrón " + padron if padron else ""}'
        f'{" código " + codigo if codigo else ""}. '
        'Todavía no se guarda en la base: falta el backend de asistencia.'
    )
    if _quiere_json():
        return jsonify({'ok': True, 'pendiente': True, 'mensaje': mensaje, 'codigo': codigo, 'padron': padron})

    flash(mensaje, 'ok')
    return redirect(url_for('web.admin.asistencia.index'))