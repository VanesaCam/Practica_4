"""
models/user.py
Modelo de usuario. No depende de Flask-Login.
"""
from models.database import get_connection


class User:
    def __init__(self, id, nombre, apellido, email, rol_id, rol_nombre,
                 xp=0, racha=0, nivel=1, activo=1):
        self.id         = id
        self.nombre     = nombre
        self.apellido   = apellido
        self.email      = email
        self.rol_id     = rol_id
        self.rol_nombre = rol_nombre
        self.xp         = xp
        self.racha      = racha
        self.nivel      = nivel
        self._activo    = activo

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def iniciales(self):
        a = self.apellido[0] if self.apellido else ''
        return (self.nombre[0] + a).upper()

    @property
    def es_admin(self):
        return self.rol_id == 1

    @property
    def es_estudiante(self):
        return self.rol_id == 2

    @property
    def nivel_label(self):
        labels = {1:'Principiante',2:'Aprendiz',3:'Basico',
                  4:'Intermedio',5:'Avanzado',6:'Experto'}
        return labels.get(self.nivel, 'Principiante')

    @staticmethod
    def get_by_id(user_id):
        conn = get_connection()
        row  = conn.execute("""
            SELECT u.id, u.nombre, u.apellido, u.email,
                   u.rol_id, r.nombre AS rol_nombre,
                   u.xp, u.racha, u.nivel, u.activo
            FROM usuarios u JOIN roles r ON r.id = u.rol_id
            WHERE u.id = ?
        """, (user_id,)).fetchone()
        conn.close()
        if row is None:
            return None
        return User(**dict(row))

    @staticmethod
    def get_by_email(email):
        conn = get_connection()
        row  = conn.execute("""
            SELECT u.id, u.nombre, u.apellido, u.email,
                   u.rol_id, r.nombre AS rol_nombre,
                   u.xp, u.racha, u.nivel, u.activo
            FROM usuarios u JOIN roles r ON r.id = u.rol_id
            WHERE u.email = ?
        """, (email,)).fetchone()
        conn.close()
        if row is None:
            return None
        return User(**dict(row))
