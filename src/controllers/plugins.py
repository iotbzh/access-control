from flask import Blueprint, redirect, render_template, request, url_for

from src.models import db, dbs, Plugin, Reader
from src.auth import admin_required
from src.plugins import Plugins

bp = Blueprint('plugins', __name__, url_prefix="/plugins")

@bp.route('/')
@admin_required
def index():
    plugins = Plugins.plugins
    return render_template('plugins/index.html', plugins=plugins.values())

@bp.route('/<plugin_uid>', methods=["GET", "POST"])
@admin_required
def view(plugin_uid):

    if request.method == "POST":
        plugin_interface = Plugins.get(plugin_uid)
        plugin_config_vars = plugin_interface.Config.__annotations__
        configs = {}

        for var in plugin_config_vars:
            configs[var] = plugin_config_vars[var](request.form.get(var))
        
        dbs.execute(db.update(Plugin).where(Plugin.uid == plugin_uid).values(configs=configs))
        dbs.commit()

    plugin_interface = Plugins.get(plugin_uid)
    plugin_config_vars = plugin_interface.Config.__annotations__
    plugin = dbs.execute(db.select(Plugin).where(Plugin.uid == plugin_uid)).scalar_one_or_none()

    if not plugin or not plugin_interface:
        return "Not found", 404

    return render_template("plugins/view.html", plugin_config_vars=plugin_config_vars, plugin=plugin, plugin_interface=plugin_interface)