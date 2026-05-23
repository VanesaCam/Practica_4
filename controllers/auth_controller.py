import time
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_connection
from models.user import User


def registrar_usuario(nombre, apellido, email, password, nivel='desde_cero'):

    if not nombre or not apellido or not email or not password:
        return False, 'Todos los campos son obligatorios.'

    if len(password) < 6:
        return False, 'La contrasena debe tener al menos 6 caracteres.'

    if '@' not in email:
        return False, 'El correo electronico no es valido.'

    conn = get_connection()

    try:

        existe = conn.execute(
            'SELECT id FROM usuarios WHERE email=?',
            (email.lower(),)
        ).fetchone()

        if existe:
            return False, 'Este correo ya esta registrado. Intenta iniciar sesion.'

        conn.execute("""
            INSERT INTO usuarios
            (nombre,apellido,email,password_hash,rol_id,ruta_aprendizaje)
            VALUES (?,?,?,?,2,?)
        """,
        (
            nombre.strip(),
            apellido.strip(),
            email.lower().strip(),
            generate_password_hash(password),
            nivel
        ))

        conn.commit()

        return True, User.get_by_email(email.lower().strip())

    except Exception as e:
        return False, f'Error: {str(e)}'

    finally:
        conn.close()


def verificar_login(email, password):

    # Verificar bloqueo temporal
    if session.get('bloqueado_hasta'):

        if time.time() < session['bloqueado_hasta']:
            return False, 'Cuenta bloqueada temporalmente. Intenta nuevamente en 60 segundos.'

        else:
            session.pop('bloqueado_hasta')
            session.pop('intentos_fallidos', None)

    if not email or not password:
        return False, 'Ingresa tu correo y contrasena.'

    conn = get_connection()

    row = conn.execute(
        'SELECT id,password_hash,activo FROM usuarios WHERE email=?',
        (email.lower().strip(),)
    ).fetchone()

    conn.close()

    # Usuario no existe
    if not row:

        session['intentos_fallidos'] = session.get('intentos_fallidos', 0) + 1

        if session['intentos_fallidos'] >= 3:

            session['bloqueado_hasta'] = time.time() + 60

            return False, 'Cuenta bloqueada por multiples intentos fallidos.'

        return False, 'No existe cuenta con ese correo.'

    # Usuario desactivado
    if not row['activo']:
        return False, 'Tu cuenta esta desactivada.'

    # Contraseña incorrecta
    if not check_password_hash(row['password_hash'], password):

        session['intentos_fallidos'] = session.get('intentos_fallidos', 0) + 1

        if session['intentos_fallidos'] >= 3:

            session['bloqueado_hasta'] = time.time() + 60

            return False, 'Cuenta bloqueada por multiples intentos fallidos.'

        return False, 'Contrasena incorrecta.'

    # Login exitoso → reiniciar contador
    session.pop('intentos_fallidos', None)
    session.pop('bloqueado_hasta', None)

    return True, User.get_by_id(row['id'])


def actualizar_perfil(user_id, nombre, apellido):

    conn = get_connection()

    conn.execute(
        'UPDATE usuarios SET nombre=?,apellido=? WHERE id=?',
        (nombre.strip(), apellido.strip(), user_id)
    )

    conn.commit()
    conn.close()
