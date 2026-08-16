from flask import Blueprint, render_template

from web.routes.admin.auth import admin_required

panel_bp = Blueprint('panel', __name__)


@panel_bp.route('/')
@admin_required
def index():
    return render_template('admin/panel.html')
