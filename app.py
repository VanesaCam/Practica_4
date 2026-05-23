"""
app.py - Punto de entrada principal de cppLearn.
Corre con: python app.py
Acceder en: http://localhost:5000
"""

from flask import Flask, session, g
from config.settings import Config
from models.database import init_db

app = Flask(__name__)
app.config.from_object(Config)


@app.before_request
def cargar_usuario():
    """Carga el usuario desde la sesion antes de cada peticion."""
    from models.user import User
    user_id = session.get('user_id')
    if user_id:
        try:
            u = User.get_by_id(int(user_id))
            g.user = u
        except Exception:
            g.user = None
            session.clear()
    else:
        g.user = None


@app.context_processor
def inject_user():
    """Hace current_user disponible en todos los templates Jinja2."""
    user = g.get('user', None)
    return dict(current_user=user)


# Registrar blueprints
from routes.auth_routes   import auth_bp
from routes.course_routes import course_bp

app.register_blueprint(auth_bp)
app.register_blueprint(course_bp)

# Crear tablas y datos iniciales al arrancar
with app.app_context():
    init_db()

if __name__ == '__main__':
    print("\n  cppLearn corriendo en: http://localhost:5000\n")
    app.run(debug=True, port=5000)
