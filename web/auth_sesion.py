"""Sesión web: destinos post-login y decoradores de acceso."""
from functools import wraps
from flask import flash, redirect, session, url_for

from web.constants import (
    PERMISO_ASISTENCIAS_GESTIONAR,
    PERMISO_ASISTENCIAS_LEER,
    PERMISO_DOCENTES_LEER,
    PERMISO_ESTUDIANTES_LEER,
)

TIPO_DOCENTE = 'docente'
TIPO_ESTUDIANTE = 'estudiante'


def usuario_sesion() -> dict:
    return session.get('usuario') or {}


def tipo_usuario() -> str:
    return usuario_sesion().get('tipo') or ''


def es_docente() -> bool:
    return tipo_usuario() == TIPO_DOCENTE


def es_estudiante() -> bool:
    return tipo_usuario() == TIPO_ESTUDIANTE

def es_super_admin() -> bool:
    return usuario_sesion().get('rol') == 'super_admin'


def es_admin() -> bool:
    return usuario_sesion().get('rol') == 'admin'


def es_superusuario() -> bool:
    return usuario_sesion().get('rol') == 'superusuario'


def puede_dar_baja() -> bool:
    """Puede dar baja si es super_admin o admin (no superusuario)."""
    return es_super_admin() or es_admin()

def permisos_sesion() -> list:
    return list(usuario_sesion().get('permisos') or [])

def tiene_permiso(codigo: str) -> bool:
    return codigo in set(permisos_sesion())

def url_login() -> str:
    return url_for('web.admin.auth.login')

def url_primera_solapa() -> str:
    """Primera solapa real que el docente puede leer. Fallback: listado."""
    if tiene_permiso(PERMISO_ESTUDIANTES_LEER):
        return url_for('web.admin.panel.index')

    if tiene_permiso(PERMISO_ASISTENCIAS_LEER) or tiene_permiso(PERMISO_ASISTENCIAS_GESTIONAR):
        return url_for('web.admin.asistencia.index')

    if tiene_permiso(PERMISO_DOCENTES_LEER):
        return url_for('web.admin.docentes.index')

    return url_for('web.admin.panel.index')

def url_post_login() -> str:
    if es_docente():
        return url_primera_solapa()

    return url_for('web.site.home.index')

def redirigir_sin_permiso(mensaje='No tenés permiso para esta acción.'):
    flash(mensaje, 'error')

    return redirect(url_primera_solapa())

def redirigir_a_login_sin_sesion():
    session.pop('token', None)
    session.pop('usuario', None)
    session.pop('nombre_completo', None)

    return redirect(url_login())


def login_required(view):
    """Zona sin /admin: hay que estar logueado. Un docente no entra acá."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('token'):
            return redirect(url_login())

        if es_docente():
            return redirect(url_for('web.admin.panel.index'))

        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """Zona /admin: hay que ser docente. Un estudiante no entra acá."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('token'):
            return redirect(url_login())

        if not es_docente():
            return redirect(url_for('web.site.home.index'))

        return view(*args, **kwargs)
        
    return wrapped