"""Autenticación del panel de administración: login, logout y el
decorador admin_required que protege las secciones internas.

El login delega la verificación de credenciales en la API (gradebook-api),
que devuelve un JWT. Ese token se guarda en la sesión y se usará para autorizar
las operaciones de administración contra la API.
"""
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session

from web.services.auth import autenticar

auth_bp = Blueprint('auth', __name__)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('token'):
            return redirect(url_for('web.admin.auth.login'))

        return view(*args, **kwargs)
    return wrapped


def redirigir_a_login_sin_sesion():
    """Limpia la sesión y redirige al login (p. ej. cuando la API responde 401/403)."""
    session.pop('token', None)
    session.pop('usuario', None)

    return redirect(url_for('web.admin.auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('token'):
        return redirect(url_for('web.admin.panel.index'))

    error = None

    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')

        resultado = autenticar(usuario, password)

        if resultado['ok']:
            session['token'] = resultado['token']
            session['usuario'] = resultado['usuario']
            return redirect(url_for('web.admin.panel.index'))

        error = resultado['error']

    return render_template('admin/login.html', error=error)


@auth_bp.route('/logout')
def logout():
    return redirigir_a_login_sin_sesion()
