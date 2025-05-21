from flask import Blueprint, redirect, render_template, request, url_for

from src.auth import login_required

bp = Blueprint('example', __name__, url_prefix="/example", template_folder="..")

@bp.route('/')
@login_required
def index():
    return render_template('example/index.html')