"""
app.py
Punto de entrada principal de cppLearn.
Usa Flask sessions nativas (sin Flask-Login) para mayor compatibilidad.
No requiere dependencias adicionales mas alla de Flask y Werkzeug.

Para correr:
    python app.py

Acceder en: http://localhost:5000
"""

from flask import Flask, session, g
from config.settings import Config
from models.database import init_db

# Crear aplicacion
app = Flask(__name__)
app.config.from_object(Config)


@app.before_request
def cargar_usuario():
    """Carga el usuario de sesion en g.user antes de cada request."""
    from models.user import User
    user_id = session.get('user_id')
    if user_id:
        g.user = User.get_by_id(user_id)
        if g.user is None:
            session.clear()
    else:
        g.user = None


@app.context_processor
def inject_user():
    """Inyecta current_user en todas las plantillas Jinja2."""
    from flask import g
    return dict(current_user=g.get('user'))


# Registrar blueprints
from routes.auth_routes   import auth_bp
from routes.course_routes import course_bp

app.register_blueprint(auth_bp)
app.register_blueprint(course_bp)

# Inicializar base de datos al arrancar
with app.app_context():
    init_db()

if __name__ == '__main__':
    print("\n  cppLearn corriendo en: http://localhost:5000\n")
    app.run(debug=True, port=5000)
