from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from controllers.auth_controller import registrar_usuario, verificar_login

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def dec(*a, **k):
        if g.get('user') is None:
            return redirect(url_for('auth.login'))
        return f(*a, **k)
    return dec

@auth_bp.route('/')
def index():
    if g.get('user'): return redirect(url_for('course.dashboard'))
    return render_template('auth/landing.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.get('user'): return redirect(url_for('course.dashboard'))
    error = None
    if request.method == 'POST':
        email = request.form.get('email','').strip()
        pw    = request.form.get('password','')
        ok, res = verificar_login(email, pw)
        if ok:
            session.clear()
            session['user_id'] = res.id
            session.permanent  = True
            return redirect(url_for('course.dashboard'))
        error = res
    return render_template('auth/login.html', error=error)

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if g.get('user'): return redirect(url_for('course.dashboard'))
    error = None
    datos = {}
    if request.method == 'POST':
        nombre   = request.form.get('nombre','').strip()
        apellido = request.form.get('apellido','').strip()
        email    = request.form.get('email','').strip()
        pw       = request.form.get('password','')
        confirm  = request.form.get('confirm','')
        nivel    = request.form.get('nivel','desde_cero')
        datos    = {'nombre':nombre,'apellido':apellido,'email':email,'nivel':nivel}
        if nivel not in ('desde_cero','intermedio','avanzado'):
            nivel = 'desde_cero'
        if pw != confirm:
            error = 'Las contrasenas no coinciden.'
        else:
            ok, res = registrar_usuario(nombre, apellido, email, pw, nivel)
            if ok:
                session.clear()
                session['user_id'] = res.id
                session.permanent  = True
                return redirect(url_for('course.dashboard'))
            error = res
    return render_template('auth/registro.html', error=error, datos=datos)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.index'))
