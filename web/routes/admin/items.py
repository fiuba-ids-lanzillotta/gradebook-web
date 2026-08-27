from flask import Blueprint, render_template, request, redirect, url_for, session

from web.routes.admin.auth import admin_required, redirigir_a_login_sin_sesion
from web.services.items import (
    obtener_items,
    body_desde_formulario,
    crear_item,
    actualizar_item,
    eliminar_item,
)

items_bp = Blueprint('items', __name__)


def _resultado_o_redirect(resultado):
    if resultado.get('ok'):
        return redirect(url_for('web.admin.items.index'))

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    return None


@items_bp.route('/items', methods=['GET', 'POST'])
@admin_required
def index():
    error = None

    if request.method == 'POST':
        resultado = crear_item(session.get('token'), body_desde_formulario(request.form))

        redireccion = _resultado_o_redirect(resultado)

        if redireccion:
            return redireccion

        error = resultado.get('error')

    return render_template('admin/items.html', items=obtener_items(), error=error)


@items_bp.route('/items/<int:item_id>/editar', methods=['POST'])
@admin_required
def editar(item_id):
    resultado = actualizar_item(
        session.get('token'),
        item_id,
        body_desde_formulario(request.form),
    )

    redireccion = _resultado_o_redirect(resultado)

    if redireccion:
        return redireccion

    return render_template('admin/items.html', items=obtener_items(), error=resultado.get('error'))


@items_bp.route('/items/<int:item_id>/eliminar', methods=['POST'])
@admin_required
def eliminar(item_id):
    resultado = eliminar_item(session.get('token'), item_id)

    redireccion = _resultado_o_redirect(resultado)
    
    if redireccion:
        return redireccion

    return render_template('admin/items.html', items=obtener_items(), error=resultado.get('error'))
