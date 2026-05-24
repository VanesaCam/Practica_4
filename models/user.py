from models.database import get_connection

class User:
    def __init__(self,id,nombre,apellido,email,rol_id,rol_nombre,
                 xp=0,racha=0,nivel=1,activo=1,ruta_aprendizaje='desde_cero'):
        self.id=id; self.nombre=nombre; self.apellido=apellido
        self.email=email; self.rol_id=rol_id; self.rol_nombre=rol_nombre
        self.xp=xp; self.racha=racha; self.nivel=nivel
        self._activo=activo; self.ruta_aprendizaje=ruta_aprendizaje

    @property
    def nombre_completo(self): return f"{self.nombre} {self.apellido}"
    @property
    def iniciales(self):
        a=self.apellido[0] if self.apellido else ''
        return (self.nombre[0]+a).upper()
    @property
    def es_admin(self): return self.rol_id==1
    @property
    def es_estudiante(self): return self.rol_id==2

    @property
    def nivel_label(self):
        """Nivel de XP del estudiante dentro del sistema."""
        return {1:'Principiante',2:'Aprendiz',3:'Basico',
                4:'Intermedio',5:'Avanzado',6:'Experto'}.get(self.nivel,'Principiante')

    @property
    def ruta_label(self):
        """Etiqueta legible de la ruta de aprendizaje elegida."""
        return {'desde_cero':  'Desde cero',
                'intermedio':  'Con conocimientos',
                'avanzado':    'Avanzado'}.get(self.ruta_aprendizaje, 'Desde cero')

    @property
    def ruta_color(self):
        """Color asociado al nivel de entrada."""
        return {'desde_cero': '#2e7d32',
                'intermedio': '#1e88e5',
                'avanzado':   '#e65100'}.get(self.ruta_aprendizaje, '#2e7d32')

    @property
    def ruta_emoji(self):
        return {'desde_cero':'📗','intermedio':'💻','avanzado':'🎯'}.get(self.ruta_aprendizaje,'📗')

    @staticmethod
    def get_by_id(uid):
        conn=get_connection()
        r=conn.execute("""SELECT u.id,u.nombre,u.apellido,u.email,u.rol_id,
            r.nombre AS rol_nombre,u.xp,u.racha,u.nivel,u.activo,u.ruta_aprendizaje
            FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.id=?""",(uid,)).fetchone()
        conn.close()
        return User(**dict(r)) if r else None

    @staticmethod
    def get_by_email(email):
        conn=get_connection()
        r=conn.execute("""SELECT u.id,u.nombre,u.apellido,u.email,u.rol_id,
            r.nombre AS rol_nombre,u.xp,u.racha,u.nivel,u.activo,u.ruta_aprendizaje
            FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.email=?""",(email,)).fetchone()
        conn.close()
        return User(**dict(r)) if r else None
