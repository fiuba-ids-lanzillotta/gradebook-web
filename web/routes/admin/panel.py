"""Inicio del panel docente: listado de alumnos del cuatrimestre actual."""
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    Response,
)

from web.auth_sesion import (
    admin_required,
    exige_permiso,
    redirigir_a_login_sin_sesion,
    tiene_permiso,
    url_primera_solapa,
    permisos_sesion,
)
from web.constants import (
    CURSADA_ANIO,
    CURSADA_CUATRIMESTRE,
    PERMISO_ASISTENCIAS_LEER,
    PERMISO_ASISTENCIAS_GESTIONAR,
    PERMISO_CURSADAS_LEER,
    PERMISO_DOCENTES_LEER,
    PERMISO_ESTUDIANTES_CREAR,
    PERMISO_ESTUDIANTES_ELIMINAR,
    PERMISO_ESTUDIANTES_LEER,
    PERMISO_ESTUDIANTES_MODIFICAR,
    PERMISO_ESTUDIANTES_REACTIVAR,
    PERMISO_EVALUACIONES_GESTIONAR,
    PERMISO_EVALUACIONES_LEER,
    PERMISO_NOTAS_LEER,
    PERMISO_REGISTROS_LEER,
)
from web.cursada_filtro import elegida, guardar, opciones
from web.services.docentes import obtener_docente
from web.services import estudiantes as servicio
from web.services import notas as notas_servicio
from web.notas_vista import preparar_categorias

panel_bp = Blueprint('panel', __name__)

ESTADO_ETIQUETA = {
    'cursando': 'Cursando',
    'abandono': 'Abandonó',
    'baja': 'Se dió de baja',
}

SOLAPAS = (
    ('cursada', 'Cursada', 'nav-cursada.svg'),
    ('listado', 'Listado alumnos', 'nav-listado.svg'),
    ('equipos', 'Listado equipos', 'nav-equipos.svg'),
    ('dashboards', 'Dashboards', 'nav-dashboards.svg'),
    ('asistencia', 'Asistencia', 'nav-asistencia.svg'),
    ('categorias', 'Categorías', 'nav-categorias.svg'),
    ('registros', 'Registros', 'nav-registros.svg'),
    ('docentes', 'Docentes', 'nav-docentes.svg'),
    ('entregas', 'Entregas', 'nav-entregas.svg'),
    ('vista', 'Vista general', 'nav-vista.svg'),
)
SOLAPA_PERMISO = {
    'cursada': PERMISO_CURSADAS_LEER,
    'listado': PERMISO_ESTUDIANTES_LEER,
    'equipos': PERMISO_ESTUDIANTES_LEER,
    'categorias': PERMISO_EVALUACIONES_LEER,
    'registros': PERMISO_REGISTROS_LEER,
    'vista': PERMISO_NOTAS_LEER,
    'asistencia': PERMISO_ASISTENCIAS_LEER,
    'docentes': PERMISO_DOCENTES_LEER,
}

def _token() -> str:
    return session.get('token') or ''


def _resultado_o_redirect(resultado):
    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if resultado.get('ok'):
        return redirect(url_for('web.admin.panel.index'))

    return None


def _nombre_docente() -> str:
    guardado = session.get('nombre_completo')

    if guardado:
        return guardado

    usuario = session.get('usuario') or {}
    docente_id = usuario.get('id')

    if not docente_id:
        return usuario.get('email') or ''

    docente = obtener_docente(_token(), docente_id).get('datos') or {}

    if docente.get('nombre') or docente.get('apellido'):
        nombre = f"{docente.get('nombre') or ''} {docente.get('apellido') or ''}".strip()
        session['nombre_completo'] = nombre

        return nombre

    return usuario.get('email') or ''

def _solapa_visible(clave: str) -> bool:
    if clave == 'asistencia':
        return tiene_permiso(PERMISO_ASISTENCIAS_LEER) or tiene_permiso(PERMISO_ASISTENCIAS_GESTIONAR)

    permiso = SOLAPA_PERMISO.get(clave)

    if permiso is None:
        return True

    return tiene_permiso(permiso)

def _alumnos_de_la_cursada(**kwargs):
    """Listado de la cursada elegida en el filtro. Si no hay, cae a la vigente."""
    activa = elegida(_token())

    return servicio.listar_de_cursada(
        _token(),
        anio=activa.get('anio'),
        cuatrimestre=activa.get('cuatrimestre'),
        **kwargs,
    )


def contexto_admin(solapa_activa: str) -> dict:
    filas = opciones(_token()) if tiene_permiso(PERMISO_CURSADAS_LEER) else []

    return {
        'permisos': permisos_sesion(),
        'nombre_docente': _nombre_docente(),
        'cursadas_filtro': filas,
        'cursada_filtro': elegida(_token(), filas) if filas else {},
        'solapas': [
            (clave, etiqueta, icono, clave == solapa_activa)
            for clave, etiqueta, icono in SOLAPAS
            if _solapa_visible(clave)
        ],
    }

def _contexto_listado(listado: dict, error=None, ok=None):
    contexto = contexto_admin('listado')
    contexto.update({
        'estudiantes': listado.get('estudiantes') or [],
        'links': listado.get('links') or {},
        'paginacion': servicio.paginas_desde_links(
            listado.get('links') or {},
            listado.get('offset', 0),
            listado.get('limit', 10),
        ),
        'q': request.args.get('q', '').strip(),
        'error': error or listado.get('error'),
        'ok': ok,
        'estado_etiqueta': ESTADO_ETIQUETA,
        'cursada_anio': listado.get('anio', CURSADA_ANIO),
        'cursada_cuatrimestre': listado.get('cuatrimestre', CURSADA_CUATRIMESTRE),
    })

    return contexto

@panel_bp.route('/cursada-activa', methods=['POST'])
@admin_required
def seleccionar_cursada():
    """Guarda la cursada del filtro global y vuelve a la pantalla de origen."""
    cursada_id = (request.form.get('cursada_id') or '').strip()
    conocida = _por_id_conocida(cursada_id)

    if conocida:
        guardar(conocida.get('id'))

    return redirect(_volver_seguro())


def _por_id_conocida(cursada_id: str) -> dict:
    if not cursada_id.isdigit():
        return {}

    for fila in opciones(_token()):
        if str(fila.get('id')) == cursada_id:
            return fila

    return {}


def _volver_seguro() -> str:
    destino = (request.form.get('volver') or '').strip()

    if destino.startswith('/') and not destino.startswith('//'):
        return destino

    return url_for('web.admin.panel.index')


@panel_bp.route('/')
@admin_required
def index():
    if not tiene_permiso(PERMISO_ESTUDIANTES_LEER):
        destino = url_primera_solapa()

        if destino != url_for('web.admin.panel.index'):
            return redirect(destino)

        return render_template(
            'admin/panel.html',
            **_contexto_listado(
                {'ok': True, 'estudiantes': [], 'links': {}},
                error='No tenés permiso para ver el listado.',
            ),
        )
    q = request.args.get('q', '').strip()

    try:
        offset = max(int(request.args.get('_offset', 0)), 0)
    except (TypeError, ValueError):
        offset = 0

    try:
        limit = max(int(request.args.get('_limit', 10)), 1)
    except (TypeError, ValueError):
        limit = 10

    listado = _alumnos_de_la_cursada(q=q, offset=offset, limit=limit)

    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    return render_template(
        'admin/panel.html',
        **_contexto_listado(listado, error=None if listado.get('ok') else listado.get('error')),
    )

@panel_bp.route('/alumnos', methods=['POST'])
@admin_required
def agregar():
    activa = elegida(_token())
    resultado = servicio.crear_estudiante(_token(), request.form, activa.get('id'))

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if resultado.get('ok'):
        destino = f" en {activa['anio']}-C{activa['cuatrimestre']}" if activa.get('anio') else ''
        flash(f'Alumno agregado e inscripto{destino}.', 'ok')
        padron = (request.form.get('padron') or '').strip()

        return redirect(url_for('web.admin.panel.index', q=padron))

    flash(resultado.get('error') or 'No se pudo agregar al alumno.', 'error')

    return redirect(url_for('web.admin.panel.index'))

@panel_bp.route('/alumnos/csv', methods=['POST'])
@admin_required
def publicar_csv():
    archivo = request.files.get('archivo')

    if archivo is None or not archivo.filename:
        flash('Elegí un archivo CSV.', 'error')

        return redirect(url_for('web.admin.panel.index'))

    resultado = servicio.importar_csv(_token(), archivo, elegida(_token()).get('id'))

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if resultado.get('ok'):
        resumen = resultado.get('resumen') or {}
        flash(
            f"CSV publicado. Nuevos: {resumen.get('estudiantes_creados', 0)}. "
            f"Inscriptos: {resumen.get('inscriptos', 0)}.",
            'ok',
        )

        return redirect(url_for('web.admin.panel.index'))

    listado = _alumnos_de_la_cursada()

    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


@panel_bp.route('/alumnos/csv', methods=['GET'])
@admin_required
def descargar_csv():
    activa = elegida(_token())
    resultado = servicio.exportar_csv(
        _token(),
        anio=activa.get('anio'),
        cuatrimestre=activa.get('cuatrimestre'),
    )

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if not resultado.get('ok'):
        flash(resultado.get('error') or 'No se pudo descargar el CSV.', 'error')

        return redirect(url_for('web.admin.panel.index'))

    return Response(
        resultado['contenido'],
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{resultado["nombre"]}"'},
    )


@panel_bp.route('/alumnos/<int:estudiante_id>/editar', methods=['POST'])
@admin_required
def editar(estudiante_id):
    resultado = servicio.actualizar_estudiante(_token(), estudiante_id, request.form)
    redireccion = _resultado_o_redirect(resultado)

    if redireccion:
        if resultado.get('ok'):
            flash('Datos del alumno actualizados.', 'ok')
        return redireccion

    listado = _alumnos_de_la_cursada()

    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


@panel_bp.route('/alumnos/<int:estudiante_id>/abandonar', methods=['POST'])
@admin_required
def abandonar(estudiante_id):
    resultado = servicio.cambiar_estado(_token(), estudiante_id, 'abandono',
                                        cursada_id=elegida(_token()).get('id'))
    redireccion = _resultado_o_redirect(resultado)

    if redireccion:
        if resultado.get('ok'):
            flash('Se marcó que el alumno abandonó la materia.', 'ok')
        return redireccion

    listado = _alumnos_de_la_cursada()

    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


@panel_bp.route('/alumnos/<int:estudiante_id>/baja', methods=['POST'])
@admin_required
def dar_de_baja(estudiante_id):
    motivo = (request.form.get('motivo') or '').strip()

    if not motivo:
        flash('La razón es obligatoria para dar de baja.', 'error')

        return redirect(url_for('web.admin.panel.index'))

    resultado = servicio.cambiar_estado(_token(), estudiante_id, 'baja', motivo,
                                        cursada_id=elegida(_token()).get('id'))
    redireccion = _resultado_o_redirect(resultado)

    if redireccion:
        if resultado.get('ok'):
            flash('Alumno dado de baja.', 'ok')
        return redireccion

    listado = _alumnos_de_la_cursada()

    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


@panel_bp.route('/alumnos/<int:estudiante_id>/alta', methods=['POST'])
@admin_required
def dar_de_alta(estudiante_id):
    bloqueo = exige_permiso(PERMISO_ESTUDIANTES_CREAR)

    if bloqueo:
        return bloqueo

    resultado = servicio.reactivar(_token(), estudiante_id, elegida(_token()).get('id'))
    redireccion = _resultado_o_redirect(resultado)

    if redireccion:
        if resultado.get('ok'):
            flash('Alumno dado de alta de nuevo.', 'ok')

        return redireccion

    listado = _alumnos_de_la_cursada()

    if listado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()
        
    return render_template('admin/panel.html', **_contexto_listado(listado, error=resultado.get('error'))), 400


def _equipo_de_vuelta():
    """Id de equipo si el perfil se abrió desde ese equipo. None si no es un id."""
    bruto = (request.values.get('equipo') or '').strip()

    if not bruto.isdigit():
        return None

    return int(bruto) or None


def _url_perfil(estudiante_id):
    equipo = _equipo_de_vuelta()

    if equipo:
        return url_for('web.admin.panel.perfil', estudiante_id=estudiante_id, equipo=equipo)

    return url_for('web.admin.panel.perfil', estudiante_id=estudiante_id)


@panel_bp.route('/alumnos/<int:estudiante_id>')
@admin_required
def perfil(estudiante_id):
    """Notas del alumno en las categorías habilitadas de la cursada elegida."""
    bloqueo = exige_permiso(PERMISO_NOTAS_LEER)

    if bloqueo:
        return bloqueo

    cursada = elegida(_token())

    if not cursada.get('id'):
        flash('Elegí una cursada para ver el perfil.', 'error')

        return redirect(url_for('web.admin.panel.index'))

    resultado = notas_servicio.calificaciones(_token(), cursada['id'], estudiante_id)

    if resultado.get('unauthorized'):
        return redirigir_a_login_sin_sesion()

    if not resultado.get('ok'):
        flash(resultado.get('error') or 'No se pudo abrir el perfil.', 'error')

        return redirect(url_for('web.admin.panel.index'))

    datos = resultado.get('datos') or {}
    puede_cargar = tiene_permiso(PERMISO_EVALUACIONES_GESTIONAR)
    categorias = preparar_categorias(datos.get('categorias') or [], puede_cargar)

    return render_template(
        'admin/perfil.html',
        estudiante=datos.get('estudiante') or {},
        categorias=categorias,
        puede_editar=any(categoria['editable'] for categoria in categorias),
        volver_equipo=_equipo_de_vuelta(),
        **contexto_admin('listado'),
    )


@panel_bp.route('/alumnos/<int:estudiante_id>/notas', methods=['POST'])
@admin_required
def guardar_nota(estudiante_id):
    """Guarda una nota de una instancia. El corrector queda como el docente logueado."""
    bloqueo = exige_permiso(PERMISO_EVALUACIONES_GESTIONAR)

    if bloqueo:
        return bloqueo

    destino = _url_perfil(estudiante_id)
    filas = _filas_nota(request.form)

    if filas is None:
        flash('No se pudieron leer las notas.', 'error')

        return redirect(destino)

    guardadas = 0

    for fila in filas:
        if fila['valor'] == fila['original'] or not fila['valor']:
            continue

        entrada = {}

        if fila['modalidad'] == 'grupal':
            if not fila['grupo_id']:
                flash('El alumno no tiene equipo en una de las categorías.', 'error')

                return redirect(destino)

            entrada['grupo_id'] = fila['grupo_id']
        else:
            entrada['estudiante_id'] = estudiante_id

        if fila['criterio'] == 'nota':
            try:
                entrada['nota'] = float(fila['valor'].replace(',', '.'))
            except ValueError:
                flash('La nota tiene que ser un número.', 'error')

                return redirect(destino)
        else:
            entrada['estado'] = fila['valor']

        resultado = notas_servicio.cargar(_token(), fila['instancia_id'], [entrada])

        if resultado.get('unauthorized'):
            return redirigir_a_login_sin_sesion()

        if not resultado.get('ok'):
            flash(resultado.get('error') or 'No se pudo guardar la nota.', 'error')

            return redirect(destino)

        guardadas += 1

    flash('Notas guardadas.' if guardadas else 'No hay cambios para guardar.', 'ok' if guardadas else 'error')

    return redirect(destino)


def _filas_nota(form) -> list | None:
    """Alinea las listas del formulario. None si no coinciden."""
    claves = ('instancia_id', 'modalidad', 'criterio', 'grupo_id', 'valor', 'original')
    columnas = {clave: form.getlist(clave) for clave in claves}
    largo = len(columnas['instancia_id'])

    if not largo or any(len(columna) != largo for columna in columnas.values()):
        return None

    filas = []

    for indice in range(largo):
        try:
            instancia_id = int(columnas['instancia_id'][indice])
            grupo_id = int(columnas['grupo_id'][indice]) if columnas['grupo_id'][indice] else None
        except ValueError:
            return None

        filas.append({
            'instancia_id': instancia_id,
            'modalidad': columnas['modalidad'][indice],
            'criterio': columnas['criterio'][indice],
            'grupo_id': grupo_id,
            'valor': columnas['valor'][indice].strip(),
            'original': columnas['original'][indice].strip(),
        })

    return filas