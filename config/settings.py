"""
config/settings.py
Configuracion central de la aplicacion.
Define rutas de base de datos, clave secreta y otros parametros globales.
"""

import os

# Directorio raiz del proyecto
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    # Clave secreta para sesiones y CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cpplearn-secret-2025-uccentral')

    # Base de datos SQLite — se guarda en la raiz del proyecto como "cpplearn.db"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'cpplearn.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # WTF CSRF
    WTF_CSRF_ENABLED = True

    # Debug
    DEBUG = True
