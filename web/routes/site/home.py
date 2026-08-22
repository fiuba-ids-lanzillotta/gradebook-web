from flask import Blueprint, render_template
from web.auth_sesion import login_required

home_bp = Blueprint('home', __name__)


@home_bp.route('/')
@login_required
def index():
    return render_template('site/inicio.html')