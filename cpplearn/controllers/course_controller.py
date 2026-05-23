"""
controllers/course_controller.py
Logica de negocio del curso:
  - Obtener modulos con progreso del usuario
  - Obtener lecciones de un modulo
  - Guardar respuesta de ejercicio
  - Calcular estadisticas del estudiante
"""

from models.database import get_connection


# ── MODULOS ──────────────────────────────────────────────────────

def obtener_modulos_con_progreso(usuario_id):
    """
    Retorna los 8 modulos con el porcentaje de avance del usuario.
    Un modulo esta bloqueado si el anterior no esta completado.
    """
    conn = get_connection()
    modulos = conn.execute("""
        SELECT m.id, m.numero, m.titulo, m.descripcion, m.nivel,
               m.total_lecciones, m.total_ejercicios,
               COALESCE(p.porcentaje, 0)  AS porcentaje,
               COALESCE(p.completado, 0)  AS completado
        FROM modulos m
        LEFT JOIN progreso p ON p.modulo_id = m.id AND p.usuario_id = ?
        WHERE m.activo = 1
        ORDER BY m.numero
    """, (usuario_id,)).fetchall()
    conn.close()

    resultado = []
    for i, m in enumerate(modulos):
        mod = dict(m)
        # El modulo 1 siempre esta disponible.
        # Los siguientes se desbloquean cuando el anterior llega a >= 50%.
        if i == 0:
            mod['bloqueado'] = False
        else:
            anterior = resultado[i - 1]
            mod['bloqueado'] = anterior['porcentaje'] < 50
        resultado.append(mod)

    return resultado


def obtener_modulo(modulo_numero):
    """Retorna datos de un modulo por su numero."""
    conn = get_connection()
    mod  = conn.execute(
        'SELECT * FROM modulos WHERE numero = ? AND activo = 1', (modulo_numero,)
    ).fetchone()
    conn.close()
    return dict(mod) if mod else None


# ── LECCIONES ────────────────────────────────────────────────────

def obtener_lecciones(modulo_id):
    """Retorna todas las lecciones de un modulo."""
    conn = get_connection()
    lecs = conn.execute(
        'SELECT * FROM lecciones WHERE modulo_id = ? ORDER BY numero',
        (modulo_id,)
    ).fetchall()
    conn.close()
    return [dict(l) for l in lecs]


def obtener_leccion(modulo_id, leccion_numero):
    """Retorna una leccion especifica."""
    conn = get_connection()
    lec  = conn.execute(
        'SELECT * FROM lecciones WHERE modulo_id = ? AND numero = ?',
        (modulo_id, leccion_numero)
    ).fetchone()
    conn.close()
    return dict(lec) if lec else None


# ── EJERCICIOS ───────────────────────────────────────────────────

def obtener_ejercicios(modulo_id, usuario_id):
    """Retorna los ejercicios de un modulo con el estado del usuario."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT e.id, e.numero, e.titulo, e.descripcion,
               e.codigo_base, e.pista, e.dificultad,
               COALESCE(r.correcto,  0) AS correcto,
               COALESCE(r.intentos,  0) AS intentos
        FROM ejercicios e
        LEFT JOIN respuestas r ON r.ejercicio_id = e.id AND r.usuario_id = ?
        WHERE e.modulo_id = ?
        ORDER BY e.numero
    """, (usuario_id, modulo_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtener_ejercicio(ejercicio_id):
    """Retorna un ejercicio con su respuesta correcta."""
    conn = get_connection()
    ej   = conn.execute('SELECT * FROM ejercicios WHERE id = ?', (ejercicio_id,)).fetchone()
    conn.close()
    return dict(ej) if ej else None


def guardar_respuesta(usuario_id, ejercicio_id, respuesta_usuario):
    """
    Compara la respuesta del usuario con la correcta.
    Guarda o actualiza en la tabla respuestas.
    Si es correcta suma 50 XP al usuario.
    Retorna (correcto: bool, xp_ganado: int).
    """
    ej = obtener_ejercicio(ejercicio_id)
    if not ej:
        return False, 0

    correcto = respuesta_usuario.strip().lower() == ej['respuesta'].strip().lower()
    xp_ganado = 0

    conn = get_connection()

    # Verificar si ya existe una respuesta previa
    existente = conn.execute(
        'SELECT id, correcto FROM respuestas WHERE usuario_id=? AND ejercicio_id=?',
        (usuario_id, ejercicio_id)
    ).fetchone()

    if existente:
        conn.execute("""
            UPDATE respuestas SET correcto=?, intentos=intentos+1, fecha=datetime('now')
            WHERE usuario_id=? AND ejercicio_id=?
        """, (1 if correcto else 0, usuario_id, ejercicio_id))
    else:
        conn.execute("""
            INSERT INTO respuestas (usuario_id, ejercicio_id, correcto)
            VALUES (?, ?, ?)
        """, (usuario_id, ejercicio_id, 1 if correcto else 0))

    # Dar XP solo si es correcto Y no lo habia respondido bien antes
    if correcto and (not existente or not existente['correcto']):
        xp_ganado = 50
        conn.execute('UPDATE usuarios SET xp = xp + 50 WHERE id = ?', (usuario_id,))
        # Actualizar nivel
        xp_row = conn.execute('SELECT xp FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
        nuevo_nivel = _calcular_nivel(xp_row['xp'])
        conn.execute('UPDATE usuarios SET nivel = ? WHERE id = ?', (nuevo_nivel, usuario_id))

    conn.commit()
    conn.close()

    # Actualizar progreso del modulo
    _actualizar_progreso_modulo(usuario_id, ej['modulo_id'])

    return correcto, xp_ganado


def _calcular_nivel(xp):
    if xp >= 5000: return 6
    if xp >= 3000: return 5
    if xp >= 1500: return 4
    if xp >= 700:  return 3
    if xp >= 200:  return 2
    return 1


def _actualizar_progreso_modulo(usuario_id, modulo_id):
    """Recalcula el porcentaje de progreso de un modulo basado en ejercicios correctos."""
    conn = get_connection()
    total_ej = conn.execute(
        'SELECT COUNT(*) AS c FROM ejercicios WHERE modulo_id = ?', (modulo_id,)
    ).fetchone()['c']

    if total_ej == 0:
        conn.close()
        return

    correctos = conn.execute("""
        SELECT COUNT(*) AS c FROM respuestas r
        JOIN ejercicios e ON e.id = r.ejercicio_id
        WHERE r.usuario_id = ? AND e.modulo_id = ? AND r.correcto = 1
    """, (usuario_id, modulo_id)).fetchone()['c']

    porcentaje = round((correctos / total_ej) * 100)
    completado = 1 if porcentaje >= 100 else 0

    conn.execute("""
        INSERT INTO progreso (usuario_id, modulo_id, porcentaje, completado)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(usuario_id, modulo_id)
        DO UPDATE SET porcentaje=excluded.porcentaje, completado=excluded.completado
    """, (usuario_id, modulo_id, porcentaje, completado))
    conn.commit()
    conn.close()


# ── ESTADISTICAS ─────────────────────────────────────────────────

def obtener_estadisticas(usuario_id):
    """Retorna un resumen del progreso del usuario."""
    conn = get_connection()

    xp_row = conn.execute(
        'SELECT xp, racha, nivel FROM usuarios WHERE id = ?', (usuario_id,)
    ).fetchone()

    totales = conn.execute("""
        SELECT
            COUNT(*)                                    AS total_ejercicios,
            SUM(CASE WHEN correcto=1 THEN 1 ELSE 0 END) AS correctos,
            SUM(CASE WHEN correcto=0 THEN 1 ELSE 0 END) AS incorrectos
        FROM respuestas WHERE usuario_id = ?
    """, (usuario_id,)).fetchone()

    mods_completados = conn.execute("""
        SELECT COUNT(*) AS c FROM progreso
        WHERE usuario_id = ? AND completado = 1
    """, (usuario_id,)).fetchone()['c']

    conn.close()

    total = totales['total_ejercicios'] or 0
    correctos = totales['correctos'] or 0
    precision = round((correctos / total) * 100) if total > 0 else 0

    return {
        'xp':                xp_row['xp']    if xp_row else 0,
        'racha':             xp_row['racha'] if xp_row else 0,
        'nivel':             xp_row['nivel'] if xp_row else 1,
        'ejercicios_resueltos': correctos,
        'ejercicios_total':  total,
        'precision':         precision,
        'modulos_completados': mods_completados,
    }


# ── ADMIN ────────────────────────────────────────────────────────

def obtener_todos_usuarios():
    """Solo para el administrador."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.id, u.nombre, u.apellido, u.email,
               u.xp, u.nivel, u.activo, r.nombre AS rol,
               u.fecha_registro
        FROM usuarios u JOIN roles r ON r.id = u.rol_id
        ORDER BY u.fecha_registro DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_usuario_activo(user_id):
    """Activa o desactiva un usuario."""
    conn = get_connection()
    conn.execute(
        'UPDATE usuarios SET activo = NOT activo WHERE id = ?', (user_id,)
    )
    conn.commit()
    conn.close()
