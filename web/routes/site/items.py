from flask import Blueprint, render_template
from web.auth_sesion import login_required
from web.services.items import obtener_items

items_bp = Blueprint('items', __name__)


@items_bp.route('/items')
@login_required
def index():
    return render_template('site/items.html', items=obtener_items())