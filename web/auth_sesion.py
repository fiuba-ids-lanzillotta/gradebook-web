"""Sesión web: destinos post-login y decoradores de acceso."""
from functools import wraps
from flask import redirect, session, url_for

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

def url_login() -> str:
    return url_for('web.admin.auth.login')


def url_post_login() -> str:
    if es_docente():
        return url_for('web.admin.panel.index')

    return url_for('web.site.home.index')


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