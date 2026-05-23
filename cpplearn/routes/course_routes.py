"""
routes/course_routes.py
Rutas del curso. Control de acceso por sesion y rol.
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, g
from functools import wraps
from controllers.course_controller import (
    obtener_modulos_con_progreso, obtener_modulo,
    obtener_lecciones, obtener_leccion,
    obtener_ejercicios, guardar_respuesta,
    obtener_estadisticas, obtener_todos_usuarios,
    toggle_usuario_activo
)

course_bp = Blueprint('course', __name__)


# DECORADORES DE ACCESO
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.get('user') is None:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def solo_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = g.get('user')
        if user is None or not user.es_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# DASHBOARD
@course_bp.route('/dashboard')
@login_required
def dashboard():
    modulos = obtener_modulos_con_progreso(g.user.id)
    stats   = obtener_estadisticas(g.user.id)
    return render_template('student/dashboard.html', modulos=modulos, stats=stats)


# MODULO
@course_bp.route('/modulo/<int:numero>')
@login_required
def modulo(numero):
    mod = obtener_modulo(numero)
    if not mod:
        abort(404)
    todos = obtener_modulos_con_progreso(g.user.id)
    mod_info = next((m for m in todos if m['numero'] == numero), None)
    if mod_info and mod_info['bloqueado']:
        return redirect(url_for('course.dashboard'))
    lecciones  = obtener_lecciones(mod['id'])
    ejercicios = obtener_ejercicios(mod['id'], g.user.id)
    stats      = obtener_estadisticas(g.user.id)
    return render_template('student/modulo.html',
                           mod=mod, lecciones=lecciones,
                           ejercicios=ejercicios, stats=stats)


# LECCION
@course_bp.route('/modulo/<int:mod_num>/leccion/<int:lec_num>')
@login_required
def leccion(mod_num, lec_num):
    mod = obtener_modulo(mod_num)
    if not mod:
        abort(404)
    lec = obtener_leccion(mod['id'], lec_num)
    if not lec:
        abort(404)
    todas    = obtener_lecciones(mod['id'])
    anterior  = next((l for l in todas if l['numero'] == lec_num - 1), None)
    siguiente = next((l for l in todas if l['numero'] == lec_num + 1), None)
    return render_template('student/leccion.html',
                           mod=mod, lec=lec,
                           anterior=anterior, siguiente=siguiente,
                           total=len(todas))


# EJERCICIO (AJAX)
@course_bp.route('/ejercicio/<int:ejercicio_id>/responder', methods=['POST'])
@login_required
def responder_ejercicio(ejercicio_id):
    data = request.get_json()
    if not data or 'respuesta' not in data:
        return jsonify({'error': 'Respuesta requerida'}), 400
    correcto, xp = guardar_respuesta(g.user.id, ejercicio_id, data['respuesta'])
    return jsonify({'correcto': correcto, 'xp_ganado': xp})


# PERFIL
@course_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    from controllers.auth_controller import actualizar_perfil
    from flask import flash
    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        if nombre and apellido:
            actualizar_perfil(g.user.id, nombre, apellido)
            flash('Perfil actualizado correctamente.', 'success')
        else:
            flash('Nombre y apellido son obligatorios.', 'error')
        return redirect(url_for('course.perfil'))
    stats = obtener_estadisticas(g.user.id)
    return render_template('student/perfil.html', stats=stats)


# ADMIN PANEL
@course_bp.route('/admin')
@login_required
@solo_admin
def admin_panel():
    usuarios = obtener_todos_usuarios()
    return render_template('admin/panel.html', usuarios=usuarios)


@course_bp.route('/admin/usuario/<int:user_id>/toggle', methods=['POST'])
@login_required
@solo_admin
def admin_toggle_usuario(user_id):
    toggle_usuario_activo(user_id)
    return redirect(url_for('course.admin_panel'))


# ERRORES
@course_bp.app_errorhandler(403)
def error_403(e):
    return render_template('shared/error.html', codigo=403,
                           mensaje='No tienes permiso para acceder a esta pagina.'), 403

@course_bp.app_errorhandler(404)
def error_404(e):
    return render_template('shared/error.html', codigo=404,
                           mensaje='La pagina que buscas no existe.'), 404
