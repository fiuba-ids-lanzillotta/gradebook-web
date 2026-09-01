"""Pantalla admin: docentes (consumo de la API real)."""
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from web.auth_sesion import admin_required, es_super_admin
from web.routes.admin.panel import contexto_admin
from web.services.docentes import (
    listar_docentes,
    crear_docente,
    actualizar_docente,
    eliminar_docente,
    actualizar_permisos_docente,
)
from web.services.permisos import obtener_catalogo_permisos
from web.constants import CARGOS
docentes_bp = Blueprint('docentes', __name__)

def _solo_profesor():
    if not es_super_admin():
        flash('Solo un profesor puede administrar docentes.', 'error')

        return redirect(url_for('web.admin.panel.index'))

    return None


def _permisos_por_cargo(catalogo: list[dict]) -> dict:
    """Calcula los permisos por cargo basado en el catálogo dinámico."""
    todos = [item['codigo'] for item in catalogo]

    return {
        'Profesor': list(todos),
        'Ayudante': [codigo for codigo in todos if codigo not in ('permisos.asignar', 'docentes.gestionar', 'estudiantes.crear', 'roles.gestionar')],
        'Colaborador': [codigo for codigo in todos if codigo not in ('permisos.asignar', 'docentes.gestionar', 'estudiantes.crear', 'estudiantes.eliminar', 'roles.gestionar')],
    }


def _contexto_pantalla(**extra) -> dict:
    token = session.get('token')
    docentes = listar_docentes(token) if token else []
    docentes_ordenados = sorted(docentes, key=lambda fila: (fila.get('apellido') or '', fila.get('nombre') or ''))
    permisos_catalogo = obtener_catalogo_permisos(token) if token else []
    permisos_por_cargo = _permisos_por_cargo(permisos_catalogo)

    return {
        **contexto_admin('docentes'),
        'docentes': docentes_ordenados,
        'cargos': CARGOS,
        'permisos_catalogo': permisos_catalogo,
        'permisos_por_cargo': permisos_por_cargo,
        **extra,
    }


@docentes_bp.route('/docentes')
@admin_required
def index():
    bloqueo = _solo_profesor()

    if bloqueo:
        return bloqueo

    return render_template('admin/docentes.html', **_contexto_pantalla())


@docentes_bp.route('/docentes', methods=['POST'])
@admin_required
def crear():
    bloqueo = _solo_profesor()

    if bloqueo:
        return bloqueo

    nombre = (request.form.get('nombre') or '').strip()
    apellido = (request.form.get('apellido') or '').strip()
    email = (request.form.get('email') or '').strip()
    rol = (request.form.get('rol') or '').strip()

    if not (nombre and apellido and email and rol in CARGOS):
        flash('Completá nombre, apellido, correo y rol.', 'error')

        return redirect(url_for('web.admin.docentes.index'))

    token = session.get('token')
    resultado = crear_docente(token, nombre, apellido, email, rol)

    if resultado:
        permisos_catalogo = obtener_catalogo_permisos(token) if token else []
        permisos_por_cargo = _permisos_por_cargo(permisos_catalogo)
        actualizar_permisos_docente(token, resultado['id'], permisos_por_cargo[rol])
        flash(f'Se agregó a {apellido}, {nombre} ({rol}). Se envió un email con la contraseña.', 'ok')
    else:
        flash('Error al crear el docente. Verificá los datos.', 'error')

    return redirect(url_for('web.admin.docentes.index'))


@docentes_bp.route('/docentes/<int:docente_id>', methods=['POST'])
@admin_required
def editar(docente_id):
    bloqueo = _solo_profesor()
    if bloqueo:
        return bloqueo

    nombre = (request.form.get('nombre') or '').strip()
    apellido = (request.form.get('apellido') or '').strip()
    email = (request.form.get('email') or '').strip()
    rol = (request.form.get('rol') or '').strip()

    if not (nombre and apellido and email and rol in CARGOS):
        flash('Completá nombre, apellido, correo y rol.', 'error')
        return redirect(url_for('web.admin.docentes.index'))

    token = session.get('token')
    resultado = actualizar_docente(token, docente_id, nombre, apellido, email, rol)

    if resultado:
        permisos_catalogo = obtener_catalogo_permisos(token) if token else []
        permisos_por_cargo = _permisos_por_cargo(permisos_catalogo)

        if rol == 'Profesor':
            permisos = list(permisos_por_cargo['Profesor'])
        else:
            tildados = set(request.form.getlist('permisos'))
            permisos = [item['codigo'] for item in permisos_catalogo if item['codigo'] in tildados]

        actualizar_permisos_docente(token, docente_id, permisos)
        flash(f'Se actualizó a {apellido}, {nombre}.', 'ok')
    else:
        flash('Error al actualizar el docente. Verificá los datos.', 'error')

    return redirect(url_for('web.admin.docentes.index'))


@docentes_bp.route('/docentes/<int:docente_id>/desactivar', methods=['POST'])
@admin_required
def desactivar(docente_id):
    bloqueo = _solo_profesor()
    if bloqueo:
        return bloqueo

    token = session.get('token')
    docentes = listar_docentes(token) if token else []
    fila = next((d for d in docentes if d.get('id') == docente_id), None)

    if not fila:
        flash('No se encontró ese docente.', 'error')

        return redirect(url_for('web.admin.docentes.index'))

    if fila.get('rol') == 'Profesor':
        flash('No se puede desactivar a un profesor.', 'error')

        return redirect(url_for('web.admin.docentes.index'))

    resultado = eliminar_docente(token, docente_id)

    if resultado:
        flash(f'{fila.get("apellido")}, {fila.get("nombre")} quedó inactivo.', 'ok')
    else:
        flash('Error al desactivar el docente.', 'error')

    return redirect(url_for('web.admin.docentes.index'))


@docentes_bp.route('/docentes/<int:docente_id>/reactivar', methods=['POST'])
@admin_required
def reactivar(docente_id):
    bloqueo = _solo_profesor()

    if bloqueo:
        return bloqueo

    token = session.get('token')
    docentes = listar_docentes(token) if token else []
    fila = next((d for d in docentes if d.get('id') == docente_id), None)

    if not fila:
        flash('No se encontró ese docente.', 'error')

        return redirect(url_for('web.admin.docentes.index'))

    flash(f'{fila.get("apellido")}, {fila.get("nombre")} volvió a estar activo (pendiente de implementación en API).', 'ok')
    
    return redirect(url_for('web.admin.docentes.index'))