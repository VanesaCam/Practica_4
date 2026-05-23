"""
controllers/course_controller.py - C++ Academy 2026
Lógica completa del curso con progreso real en porcentaje,
retomar automático, admin separado y ejercicios completos.
"""
from models.database import get_connection

MODULOS_POR_NIVEL = {
    'desde_cero': [1,2,3,4,5,6,7,8,9],
    'intermedio':  [4,5,6,7,8,9],
    'avanzado':    [7,8,9],
}

# ── MÓDULOS ──────────────────────────────────────────────────────
def obtener_modulos_con_progreso(usuario_id, nivel='desde_cero', es_admin=False):
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.id, m.numero, m.titulo, m.descripcion, m.nivel,
               m.total_lecciones, m.total_ejercicios,
               COALESCE(p.porcentaje, 0) AS porcentaje,
               COALESCE(p.completado, 0) AS completado
        FROM modulos m
        LEFT JOIN progreso p ON p.modulo_id=m.id AND p.usuario_id=?
        WHERE m.activo=1 ORDER BY m.numero
    """, (usuario_id,)).fetchall()
    conn.close()

    accesibles = MODULOS_POR_NIVEL.get(nivel, [1,2,3,4,5,6,7,8,9])
    resultado = []
    for m in rows:
        mod = dict(m)
        if es_admin:
            mod['bloqueado']   = False
            mod['fuera_nivel'] = False
        elif mod['numero'] not in accesibles:
            mod['bloqueado']   = True
            mod['fuera_nivel'] = True
        else:
            mod['fuera_nivel'] = False
            idx = accesibles.index(mod['numero'])
            if idx == 0:
                mod['bloqueado'] = False
            else:
                prev = next((r for r in resultado if r['numero'] == accesibles[idx-1]), None)
                mod['bloqueado'] = (not prev) or prev['bloqueado'] or prev['porcentaje'] < 40
        resultado.append(mod)
    return resultado

def obtener_modulo(numero):
    conn = get_connection()
    r = conn.execute('SELECT * FROM modulos WHERE numero=? AND activo=1', (numero,)).fetchone()
    conn.close()
    return dict(r) if r else None

# ── LECCIONES ────────────────────────────────────────────────────
def obtener_lecciones(modulo_id, usuario_id=None):
    conn = get_connection()
    rows = conn.execute(
        'SELECT * FROM lecciones WHERE modulo_id=? ORDER BY numero', (modulo_id,)
    ).fetchall()
    lecs = [dict(r) for r in rows]
    if usuario_id:
        for lec in lecs:
            c = conn.execute(
                'SELECT completada FROM lecciones_completadas WHERE usuario_id=? AND leccion_id=?',
                (usuario_id, lec['id'])
            ).fetchone()
            lec['completada'] = bool(c and c['completada'])
    conn.close()
    return lecs

def obtener_leccion(modulo_id, numero):
    conn = get_connection()
    r = conn.execute(
        'SELECT * FROM lecciones WHERE modulo_id=? AND numero=?', (modulo_id, numero)
    ).fetchone()
    conn.close()
    return dict(r) if r else None

def marcar_leccion_completada(usuario_id, leccion_id, modulo_id):
    conn = get_connection()
    conn.execute("""
        INSERT INTO lecciones_completadas(usuario_id, leccion_id, completada)
        VALUES(?,?,1)
        ON CONFLICT(usuario_id, leccion_id)
        DO UPDATE SET completada=1, fecha=datetime('now')
    """, (usuario_id, leccion_id))
    # Guardar posición para retomar
    conn.execute(
        "UPDATE usuarios SET ultimo_modulo=?, ultima_leccion=? WHERE id=?",
        (modulo_id, leccion_id, usuario_id)
    )
    conn.commit()
    conn.close()
    _recalcular_progreso(usuario_id, modulo_id)

def _recalcular_progreso(usuario_id, modulo_id):
    conn = get_connection()
    total_lec = conn.execute(
        'SELECT COUNT(*) AS c FROM lecciones WHERE modulo_id=?', (modulo_id,)
    ).fetchone()['c']
    total_ej = conn.execute(
        'SELECT COUNT(*) AS c FROM ejercicios WHERE modulo_id=?', (modulo_id,)
    ).fetchone()['c']
    comp_lec = conn.execute("""
        SELECT COUNT(*) AS c FROM lecciones_completadas lc
        JOIN lecciones l ON l.id=lc.leccion_id
        WHERE lc.usuario_id=? AND l.modulo_id=? AND lc.completada=1
    """, (usuario_id, modulo_id)).fetchone()['c']
    comp_ej = conn.execute("""
        SELECT COUNT(*) AS c FROM respuestas r
        JOIN ejercicios e ON e.id=r.ejercicio_id
        WHERE r.usuario_id=? AND e.modulo_id=? AND r.correcto=1
    """, (usuario_id, modulo_id)).fetchone()['c']

    total      = (total_lec + total_ej) or 1
    completados = comp_lec + comp_ej
    pct         = round((completados / total) * 100)
    # Limitar a 100 por si hay datos duplicados
    pct = min(pct, 100)
    conn.execute("""
        INSERT INTO progreso(usuario_id, modulo_id, porcentaje, completado)
        VALUES(?,?,?,?)
        ON CONFLICT(usuario_id, modulo_id)
        DO UPDATE SET porcentaje=excluded.porcentaje, completado=excluded.completado
    """, (usuario_id, modulo_id, pct, 1 if pct >= 100 else 0))
    conn.commit()
    conn.close()

def obtener_progreso_leccion(usuario_id, modulo_id):
    """Porcentaje de lecciones completadas en un módulo."""
    conn = get_connection()
    total = conn.execute(
        'SELECT COUNT(*) AS c FROM lecciones WHERE modulo_id=?', (modulo_id,)
    ).fetchone()['c']
    comp = conn.execute("""
        SELECT COUNT(*) AS c FROM lecciones_completadas lc
        JOIN lecciones l ON l.id=lc.leccion_id
        WHERE lc.usuario_id=? AND l.modulo_id=? AND lc.completada=1
    """, (usuario_id, modulo_id)).fetchone()['c']
    conn.close()
    return {'completadas': comp, 'total': total,
            'porcentaje': round((comp / total) * 100) if total else 0}

# ── EJERCICIOS ───────────────────────────────────────────────────
def obtener_todos_ejercicios(modulo_id, usuario_id, es_admin=False):
    """
    Retorna TODOS los ejercicios del módulo con su estado.
    Los bloqueados se marcan pero se incluyen en la lista.
    Admin: ve todo incluidas respuestas correctas.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT e.id, e.numero, e.titulo, e.descripcion, e.codigo_base,
               e.opcion_a, e.opcion_b, e.opcion_c, e.opcion_d,
               e.pista, e.dificultad, e.explicacion,
               CASE WHEN ? THEN e.respuesta_correcta ELSE NULL END AS respuesta_correcta,
               COALESCE(r.correcto, 0)      AS correcto,
               COALESCE(r.intentos, 0)      AS intentos,
               COALESCE(r.respuesta_dada,'') AS respuesta_dada
        FROM ejercicios e
        LEFT JOIN respuestas r ON r.ejercicio_id=e.id AND r.usuario_id=?
        WHERE e.modulo_id=? ORDER BY e.numero
    """, (1 if es_admin else 0, usuario_id, modulo_id)).fetchall()
    conn.close()

    ejercicios = [dict(r) for r in rows]
    for i, ej in enumerate(ejercicios):
        if es_admin:
            ej['desbloqueado'] = True
        elif i == 0:
            ej['desbloqueado'] = True
        else:
            ej['desbloqueado'] = ejercicios[i-1]['correcto'] == 1
    return ejercicios

# Mantener nombre anterior como alias
obtener_ejercicios_desbloqueados = obtener_todos_ejercicios

def obtener_ejercicio(eid):
    conn = get_connection()
    r = conn.execute('SELECT * FROM ejercicios WHERE id=?', (eid,)).fetchone()
    conn.close()
    return dict(r) if r else None

def guardar_respuesta(usuario_id, ejercicio_id, respuesta_dada):
    ej = obtener_ejercicio(ejercicio_id)
    if not ej: return False, 0
    correcto = respuesta_dada.strip().lower() == ej['respuesta_correcta'].strip().lower()
    conn = get_connection()
    existente = conn.execute(
        'SELECT id, correcto FROM respuestas WHERE usuario_id=? AND ejercicio_id=?',
        (usuario_id, ejercicio_id)
    ).fetchone()
    if existente:
        conn.execute("""
            UPDATE respuestas SET correcto=?, intentos=intentos+1,
            respuesta_dada=?, fecha=datetime('now')
            WHERE usuario_id=? AND ejercicio_id=?
        """, (1 if correcto else 0, respuesta_dada, usuario_id, ejercicio_id))
    else:
        conn.execute(
            "INSERT INTO respuestas(usuario_id,ejercicio_id,correcto,respuesta_dada) VALUES(?,?,?,?)",
            (usuario_id, ejercicio_id, 1 if correcto else 0, respuesta_dada)
        )
    xp = 0
    if correcto and (not existente or not existente['correcto']):
        xp = 50
        conn.execute('UPDATE usuarios SET xp=xp+50 WHERE id=?', (usuario_id,))
        xp_r = conn.execute('SELECT xp FROM usuarios WHERE id=?', (usuario_id,)).fetchone()
        conn.execute('UPDATE usuarios SET nivel=? WHERE id=?', (_nv(xp_r['xp']), usuario_id))
    conn.commit()
    conn.close()
    if ej.get('modulo_id'):
        _recalcular_progreso(usuario_id, ej['modulo_id'])
    return correcto, xp

def _nv(xp):
    for n, x in [(6,5000),(5,3000),(4,1500),(3,700),(2,200)]:
        if xp >= x: return n
    return 1

# ── RETOMAR ──────────────────────────────────────────────────────
def obtener_punto_retomar(usuario_id, ruta_aprendizaje):
    conn = get_connection()
    u = conn.execute(
        'SELECT ultimo_modulo, ultima_leccion FROM usuarios WHERE id=?', (usuario_id,)
    ).fetchone()
    conn.close()
    if not u or not u['ultimo_modulo']:
        primer = MODULOS_POR_NIVEL.get(ruta_aprendizaje, [1])[0]
        return {'modulo_numero': primer, 'leccion_numero': 1, 'tipo': 'inicio'}
    conn = get_connection()
    mod = conn.execute('SELECT * FROM modulos WHERE id=?', (u['ultimo_modulo'],)).fetchone()
    lec = conn.execute('SELECT * FROM lecciones WHERE id=?', (u['ultima_leccion'],)).fetchone() if u['ultima_leccion'] else None

    # Buscar la SIGUIENTE lección no completada en ese módulo
    sig = None
    if lec and mod:
        sig = conn.execute("""
            SELECT l.* FROM lecciones l
            WHERE l.modulo_id=? AND l.numero > ?
            AND NOT EXISTS(
                SELECT 1 FROM lecciones_completadas lc
                WHERE lc.leccion_id=l.id AND lc.usuario_id=? AND lc.completada=1
            )
            ORDER BY l.numero LIMIT 1
        """, (mod['id'], lec['numero'], usuario_id)).fetchone()
    conn.close()

    if sig and mod:
        return {'modulo_numero': mod['numero'], 'leccion_numero': sig['numero'],
                'tipo': 'retomar', 'modulo_titulo': mod['titulo'],
                'leccion_titulo': sig['titulo']}
    elif mod:
        return {'modulo_numero': mod['numero'], 'leccion_numero': 1,
                'tipo': 'retomar', 'modulo_titulo': mod['titulo'], 'leccion_titulo': ''}
    primer = MODULOS_POR_NIVEL.get(ruta_aprendizaje, [1])[0]
    return {'modulo_numero': primer, 'leccion_numero': 1, 'tipo': 'inicio'}

# ── ESTADÍSTICAS ─────────────────────────────────────────────────
def obtener_estadisticas(usuario_id):
    conn = get_connection()
    u  = conn.execute('SELECT xp, racha, nivel FROM usuarios WHERE id=?', (usuario_id,)).fetchone()
    t  = conn.execute("""
        SELECT COUNT(*) AS tot,
               SUM(CASE WHEN correcto=1 THEN 1 ELSE 0 END) AS ok
        FROM respuestas WHERE usuario_id=?
    """, (usuario_id,)).fetchone()
    lc = conn.execute(
        "SELECT COUNT(*) AS c FROM lecciones_completadas WHERE usuario_id=? AND completada=1",
        (usuario_id,)
    ).fetchone()
    mc = conn.execute(
        "SELECT COUNT(*) AS c FROM progreso WHERE usuario_id=? AND completado=1",
        (usuario_id,)
    ).fetchone()
    conn.close()
    tot = t['tot'] or 0
    ok  = t['ok']  or 0
    return {
        'xp':                   u['xp']    if u else 0,
        'racha':                u['racha'] if u else 0,
        'nivel':                u['nivel'] if u else 1,
        'ejercicios_resueltos': ok,
        'ejercicios_total':     tot,
        'precision':            round((ok / tot) * 100) if tot else 0,
        'modulos_completados':  mc['c'],
        'lecciones_completadas':lc['c'],
    }

# ── PROYECTO FINAL ───────────────────────────────────────────────
def obtener_proyecto(usuario_id):
    conn = get_connection()
    r = conn.execute('SELECT * FROM proyecto_final WHERE usuario_id=?', (usuario_id,)).fetchone()
    conn.close()
    return dict(r) if r else None

def guardar_proyecto(usuario_id, tipo, descripcion,
                     archivo_nombre=None, archivo_ruta=None,
                     captura_nombre=None, captura_ruta=None):
    conn = get_connection()
    existe = conn.execute(
        'SELECT id FROM proyecto_final WHERE usuario_id=?', (usuario_id,)
    ).fetchone()
    if existe:
        conn.execute("""
            UPDATE proyecto_final SET tipo_proyecto=?, descripcion_entregada=?,
            archivo_nombre=?, archivo_ruta=?, captura_nombre=?, captura_ruta=?,
            estado='entregado', fecha_entrega=datetime('now') WHERE usuario_id=?
        """, (tipo, descripcion, archivo_nombre, archivo_ruta,
              captura_nombre, captura_ruta, usuario_id))
    else:
        conn.execute("""
            INSERT INTO proyecto_final(usuario_id, tipo_proyecto, descripcion_entregada,
            archivo_nombre, archivo_ruta, captura_nombre, captura_ruta, estado)
            VALUES(?,?,?,?,?,?,?,'entregado')
        """, (usuario_id, tipo, descripcion, archivo_nombre, archivo_ruta,
              captura_nombre, captura_ruta))
    conn.commit()
    conn.close()

# ── ADMIN ─────────────────────────────────────────────────────────
def obtener_todos_usuarios():
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.id, u.nombre, u.apellido, u.email, u.xp, u.nivel,
               u.activo, u.ruta_aprendizaje, r.nombre AS rol, u.fecha_registro
        FROM usuarios u JOIN roles r ON r.id=u.rol_id
        ORDER BY u.fecha_registro DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def obtener_certificados_emitidos():
    """Lista de usuarios que tienen 100% en todos sus módulos."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT u.id, u.nombre, u.apellido, u.email, u.xp, u.ruta_aprendizaje,
               u.fecha_registro,
               COUNT(p.id) AS mods_completados
        FROM usuarios u
        LEFT JOIN progreso p ON p.usuario_id=u.id AND p.completado=1
        WHERE u.rol_id=2
        GROUP BY u.id
        ORDER BY u.fecha_registro DESC
    """).fetchall()
    conn.close()
    resultado = []
    modulos_requeridos = {'desde_cero': 9, 'intermedio': 6, 'avanzado': 3}
    for r in rows:
        d = dict(r)
        req = modulos_requeridos.get(d['ruta_aprendizaje'], 9)
        d['tiene_certificado'] = d['mods_completados'] >= req
        d['modulos_requeridos'] = req
        resultado.append(d)
    return resultado

def obtener_progreso_estudiante(uid):
    conn = get_connection()
    mp = conn.execute("""
        SELECT m.numero, m.titulo, m.nivel,
               COALESCE(p.porcentaje, 0) AS porcentaje,
               COALESCE(p.completado, 0) AS completado,
               (SELECT COUNT(*) FROM lecciones WHERE modulo_id=m.id) AS total_lec,
               (SELECT COUNT(*) FROM lecciones_completadas lc
                JOIN lecciones l ON l.id=lc.leccion_id
                WHERE lc.usuario_id=? AND l.modulo_id=m.id AND lc.completada=1) AS comp_lec,
               (SELECT COUNT(*) FROM ejercicios WHERE modulo_id=m.id) AS total_ej,
               (SELECT COUNT(*) FROM respuestas r
                JOIN ejercicios e ON e.id=r.ejercicio_id
                WHERE r.usuario_id=? AND e.modulo_id=m.id AND r.correcto=1) AS comp_ej
        FROM modulos m
        LEFT JOIN progreso p ON p.modulo_id=m.id AND p.usuario_id=?
        ORDER BY m.numero
    """, (uid, uid, uid)).fetchall()
    rs = conn.execute("""
        SELECT e.titulo AS ejercicio, m.titulo AS modulo,
               r.correcto, r.intentos, r.respuesta_dada,
               e.respuesta_correcta, r.fecha
        FROM respuestas r
        JOIN ejercicios e ON e.id=r.ejercicio_id
        JOIN modulos m ON m.id=e.modulo_id
        WHERE r.usuario_id=? ORDER BY r.fecha DESC
    """, (uid,)).fetchall()
    conn.close()
    return [dict(r) for r in mp], [dict(r) for r in rs]

def toggle_usuario_activo(uid):
    conn = get_connection()
    conn.execute('UPDATE usuarios SET activo=NOT activo WHERE id=?', (uid,))
    conn.commit()
    conn.close()
