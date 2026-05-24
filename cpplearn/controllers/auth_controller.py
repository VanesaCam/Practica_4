"""
controllers/auth_controller.py
Logica de negocio para autenticacion:
  - Registro de nuevos usuarios
  - Validacion de credenciales en login
  - Actualizacion de perfil
"""

from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_connection
from models.user import User


def registrar_usuario(nombre, apellido, email, password):
    """
    Crea un nuevo usuario con rol Estudiante (rol_id=2).
    Retorna (True, usuario) si exitoso o (False, mensaje_error) si falla.
    """
    # Validaciones basicas
    if not nombre or not apellido or not email or not password:
        return False, 'Todos los campos son obligatorios.'
    if len(password) < 6:
        return False, 'La contrasena debe tener al menos 6 caracteres.'
    if '@' not in email or '.' not in email:
        return False, 'El correo electronico no es valido.'

    conn = get_connection()
    try:
        # Verificar correo duplicado
        existe = conn.execute(
            'SELECT id FROM usuarios WHERE email = ?', (email.lower(),)
        ).fetchone()
        if existe:
            return False, 'Este correo electronico ya esta registrado.'

        # Encriptar contrasena con Werkzeug (usa pbkdf2:sha256)
        pw_hash = generate_password_hash(password)

        conn.execute("""
            INSERT INTO usuarios (nombre, apellido, email, password_hash, rol_id)
            VALUES (?, ?, ?, ?, 2)
        """, (nombre.strip(), apellido.strip(), email.lower().strip(), pw_hash))
        conn.commit()

        # Retornar el usuario recien creado
        usuario = User.get_by_email(email.lower().strip())
        return True, usuario

    except Exception as e:
        return False, f'Error interno: {str(e)}'
    finally:
        conn.close()


def verificar_login(email, password):
    """
    Verifica credenciales.
    Retorna (True, usuario) si son correctas o (False, mensaje) si no.
    """
    if not email or not password:
        return False, 'Ingresa tu correo y contrasena.'

    conn = get_connection()
    row  = conn.execute(
        'SELECT id, password_hash, activo FROM usuarios WHERE email = ?',
        (email.lower().strip(),)
    ).fetchone()
    conn.close()

    if row is None:
        return False, 'No existe una cuenta con ese correo electronico.'
    if not row['activo']:
        return False, 'Tu cuenta esta desactivada. Contacta al administrador.'
    if not check_password_hash(row['password_hash'], password):
        return False, 'Contrasena incorrecta.'

    usuario = User.get_by_id(row['id'])
    return True, usuario


def actualizar_perfil(user_id, nombre, apellido):
    """Actualiza nombre y apellido del usuario."""
    conn = get_connection()
    conn.execute(
        'UPDATE usuarios SET nombre = ?, apellido = ? WHERE id = ?',
        (nombre.strip(), apellido.strip(), user_id)
    )
    conn.commit()
    conn.close()
