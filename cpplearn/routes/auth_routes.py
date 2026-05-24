"""
routes/auth_routes.py
Rutas de autenticacion usando Flask session nativa (sin Flask-Login).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from controllers.auth_controller import registrar_usuario, verificar_login

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorador: redirige al login si el usuario no tiene sesion activa."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.get('user') is None:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/')
def index():
    if g.get('user'):
        return redirect(url_for('course.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.get('user'):
        return redirect(url_for('course.dashboard'))

    error = None
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        ok, resultado = verificar_login(email, password)
        if ok:
            session.clear()
            session['user_id'] = resultado.id
            session.permanent = True
            return redirect(url_for('course.dashboard'))
        else:
            error = resultado

    return render_template('auth/login.html', error=error)


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if g.get('user'):
        return redirect(url_for('course.dashboard'))

    error = None
    datos = {}

    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')
        datos    = {'nombre': nombre, 'apellido': apellido, 'email': email}

        if password != confirm:
            error = 'Las contrasenas no coinciden.'
        else:
            ok, resultado = registrar_usuario(nombre, apellido, email, password)
            if ok:
                session.clear()
                session['user_id'] = resultado.id
                session.permanent = True
                flash('Cuenta creada correctamente. Bienvenido/a!', 'success')
                return redirect(url_for('course.dashboard'))
            else:
                error = resultado

    return render_template('auth/registro.html', error=error, datos=datos)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
