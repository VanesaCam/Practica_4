import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, g, flash
from controllers.course_controller import *
from models.database import UPLOAD_PATH

course_bp = Blueprint('course', __name__)

def login_required(f):
    @wraps(f)
    def dec(*a, **k):
        if g.get('user') is None:
            return redirect(url_for('auth.login'))
        return f(*a, **k)
    return dec

def solo_admin(f):
    @wraps(f)
    def dec(*a, **k):
        if not g.get('user') or not g.user.es_admin:
            abort(403)
        return f(*a, **k)
    return dec

# ── DASHBOARD ────────────────────────────────────────────────────
@course_bp.route('/dashboard')
@login_required
def dashboard():
    u = g.user
    modulos = obtener_modulos_con_progreso(u.id, u.ruta_aprendizaje, u.es_admin)
    stats   = obtener_estadisticas(u.id)
    retomar = obtener_punto_retomar(u.id, u.ruta_aprendizaje)
    return render_template('student/dashboard.html',
                           modulos=modulos, stats=stats, retomar=retomar)

# ── MÓDULO ───────────────────────────────────────────────────────
@course_bp.route('/modulo/<int:numero>')
@login_required
def modulo(numero):
    mod = obtener_modulo(numero)
    if not mod: abort(404)

    if not g.user.es_admin:
        todos = obtener_modulos_con_progreso(g.user.id, g.user.ruta_aprendizaje, False)
        mi = next((m for m in todos if m['numero'] == numero), None)
        if mi and mi.get('fuera_nivel'):
            flash('Este modulo no corresponde a tu nivel de entrada.', 'info')
            return redirect(url_for('course.dashboard'))
        if mi and mi['bloqueado']:
            flash('Completa el modulo anterior para desbloquear este.', 'info')
            return redirect(url_for('course.dashboard'))

    lecciones  = obtener_lecciones(mod['id'], g.user.id)
    ejercicios = obtener_todos_ejercicios(mod['id'], g.user.id, g.user.es_admin)
    stats      = obtener_estadisticas(g.user.id)
    prog_lec   = obtener_progreso_leccion(g.user.id, mod['id'])
    total_lecs = len(lecciones)
    lecs_ok    = sum(1 for l in lecciones if l.get('completada'))

    return render_template('student/modulo.html',
                           mod=mod, lecciones=lecciones, ejercicios=ejercicios,
                           stats=stats, prog_lec=prog_lec,
                           total_lecs=total_lecs, lecs_completadas=lecs_ok)

# ── LECCIÓN ──────────────────────────────────────────────────────
@course_bp.route('/modulo/<int:mn>/leccion/<int:ln>')
@login_required
def leccion(mn, ln):
    mod = obtener_modulo(mn)
    if not mod: abort(404)
    lec = obtener_leccion(mod['id'], ln)
    if not lec: abort(404)
    todas    = obtener_lecciones(mod['id'], g.user.id)
    ant      = next((l for l in todas if l['numero'] == ln - 1), None)
    sig      = next((l for l in todas if l['numero'] == ln + 1), None)
    prog_lec = obtener_progreso_leccion(g.user.id, mod['id'])
    return render_template('student/leccion.html',
                           mod=mod, lec=lec, anterior=ant, siguiente=sig,
                           total=len(todas), todas=todas, prog_lec=prog_lec)

# ── COMPLETAR LECCIÓN (AJAX) ─────────────────────────────────────
@course_bp.route('/leccion/<int:lid>/completar', methods=['POST'])
@login_required
def completar_leccion(lid):
    conn = __import__('models.database', fromlist=['get_connection']).get_connection()
    lec  = conn.execute('SELECT * FROM lecciones WHERE id=?', (lid,)).fetchone()
    if not lec:
        conn.close()
        return jsonify({'error': 'no encontrada'}), 404
    mod = conn.execute('SELECT numero FROM modulos WHERE id=?', (lec['modulo_id'],)).fetchone()
    sig = conn.execute(
        'SELECT * FROM lecciones WHERE modulo_id=? AND numero>? ORDER BY numero LIMIT 1',
        (lec['modulo_id'], lec['numero'])
    ).fetchone()
    conn.close()

    marcar_leccion_completada(g.user.id, lid, lec['modulo_id'])
    prog = obtener_progreso_leccion(g.user.id, lec['modulo_id'])

    return jsonify({
        'ok': True,
        'porcentaje_lecciones': prog['porcentaje'],
        'completadas':          prog['completadas'],
        'total_lecciones':      prog['total'],
        'siguiente_leccion':    {'numero': sig['numero'], 'titulo': sig['titulo']} if sig else None,
        'modulo_numero':        mod['numero'] if mod else None,
        'es_ultima':            sig is None,
    })

# ── RESPONDER EJERCICIO (AJAX) ────────────────────────────────────
@course_bp.route('/ejercicio/<int:eid>/responder', methods=['POST'])
@login_required
def responder(eid):
    data = request.get_json()
    if not data or 'respuesta' not in data:
        return jsonify({'error': 'requerido'}), 400

    ok, xp = guardar_respuesta(g.user.id, eid, data['respuesta'])
    ej     = obtener_ejercicio(eid)

    # Siguiente ejercicio en mismo módulo
    siguiente_id = None
    if ok and ej:
        conn = __import__('models.database', fromlist=['get_connection']).get_connection()
        sig  = conn.execute(
            "SELECT id FROM ejercicios WHERE modulo_id=? AND numero>? ORDER BY numero LIMIT 1",
            (ej['modulo_id'], ej['numero'])
        ).fetchone()
        conn.close()
        if sig: siguiente_id = sig['id']

    # Retroalimentación específica por opción elegida
    clave  = data['respuesta'].lower()
    mapa   = {'a': 'opcion_a', 'b': 'opcion_b', 'c': 'opcion_c', 'd': 'opcion_d'}
    campo  = mapa.get(clave, '')
    texto_elegido  = ej.get(campo, '') if ej else ''
    resp_correcta  = ej.get('respuesta_correcta', '') if ej else ''
    campo_correcto = mapa.get(resp_correcta, '')
    texto_correcto = ej.get(campo_correcto, '') if ej else ''

    retro = ''
    if not ok and ej:
        retro = (
            f"La opcion {clave.upper()} ({texto_elegido}) no es la respuesta correcta. "
            f"La respuesta correcta es la opcion {resp_correcta.upper()} ({texto_correcto}). "
            f"{ej.get('explicacion', '')}"
        )

    # XP actualizado desde BD
    from models.user import User
    u_actual = User.get_by_id(g.user.id)

    # Progreso actualizado del módulo
    prog_mod = {'porcentaje': 0}
    if ej and ej.get('modulo_id'):
        conn = __import__('models.database', fromlist=['get_connection']).get_connection()
        p = conn.execute(
            'SELECT porcentaje FROM progreso WHERE usuario_id=? AND modulo_id=?',
            (g.user.id, ej['modulo_id'])
        ).fetchone()
        conn.close()
        if p: prog_mod['porcentaje'] = p['porcentaje']

    return jsonify({
        'correcto':          ok,
        'xp_ganado':         xp,
        'xp_total':          u_actual.xp if u_actual else g.user.xp,
        'explicacion':       ej['explicacion'] if ej else '',
        'retroalimentacion': retro,
        'respuesta_correcta':resp_correcta,
        'texto_correcto':    texto_correcto,
        'siguiente_id':      siguiente_id,
        'progreso_modulo':   prog_mod['porcentaje'],
    })

# ── PROGRESO EN TIEMPO REAL (AJAX) ───────────────────────────────
@course_bp.route('/api/progreso/<int:modulo_id>')
@login_required
def api_progreso(modulo_id):
    prog_lec = obtener_progreso_leccion(g.user.id, modulo_id)
    conn = __import__('models.database', fromlist=['get_connection']).get_connection()
    p = conn.execute(
        'SELECT porcentaje FROM progreso WHERE usuario_id=? AND modulo_id=?',
        (g.user.id, modulo_id)
    ).fetchone()
    conn.close()
    return jsonify({
        'lecciones':         prog_lec,
        'porcentaje_modulo': p['porcentaje'] if p else 0,
    })

# ── PERFIL ───────────────────────────────────────────────────────
@course_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    from controllers.auth_controller import actualizar_perfil
    if request.method == 'POST':
        n = request.form.get('nombre', '').strip()
        a = request.form.get('apellido', '').strip()
        if n and a:
            actualizar_perfil(g.user.id, n, a)
            flash('Perfil actualizado.', 'success')
        else:
            flash('Nombre y apellido son obligatorios.', 'error')
        return redirect(url_for('course.perfil'))
    stats   = obtener_estadisticas(g.user.id)
    modulos = obtener_modulos_con_progreso(g.user.id, g.user.ruta_aprendizaje, g.user.es_admin)
    retomar = obtener_punto_retomar(g.user.id, g.user.ruta_aprendizaje)
    return render_template('student/perfil.html',
                           stats=stats, modulos=modulos, retomar=retomar)

# ── CERTIFICADO ──────────────────────────────────────────────────
@course_bp.route('/certificado')
@login_required
def certificado():
    # Admin: ver historial de certificados de estudiantes
    if g.user.es_admin:
        certs = obtener_certificados_emitidos()
        return render_template('admin/certificados.html', certificados=certs)

    u           = g.user
    modulos     = obtener_modulos_con_progreso(u.id, u.ruta_aprendizaje, False)
    mods_ruta   = MODULOS_POR_NIVEL.get(u.ruta_aprendizaje, [1,2,3,4,5,6,7,8,9])
    mods_usuario= [m for m in modulos if m['numero'] in mods_ruta]
    completados = [m for m in mods_usuario if m['completado']]
    total_ruta  = len(mods_ruta)
    total_comp  = len(completados)
    proyecto    = obtener_proyecto(u.id)
    nec_proyecto= u.ruta_aprendizaje == 'avanzado'
    proyecto_ok = (not nec_proyecto) or (proyecto and proyecto['estado'] == 'entregado')
    puede_cert  = total_comp >= total_ruta and proyecto_ok
    stats       = obtener_estadisticas(u.id)

    import datetime
    return render_template('student/certificado.html',
                           u=u, stats=stats,
                           puede_certificado=puede_cert,
                           total_ruta=total_ruta, total_completos=total_comp,
                           mods_usuario=mods_usuario, proyecto=proyecto,
                           necesita_proyecto=nec_proyecto, proyecto_ok=proyecto_ok,
                           fecha_hoy=datetime.date.today().strftime("%d de %B de %Y"),
                           folio=f"CPP-2026-{u.id:04d}")

# ── PROYECTO FINAL ────────────────────────────────────────────────
@course_bp.route('/proyecto', methods=['GET', 'POST'])
@login_required
def proyecto():
    if request.method == 'POST':
        tipo        = request.form.get('tipo_proyecto', 'calculadora')
        descripcion = request.form.get('descripcion', '').strip()
        arch_n = arch_r = cap_n = cap_r = None

        if 'archivo_cpp' in request.files:
            f = request.files['archivo_cpp']
            if f and f.filename:
                import uuid
                ext = os.path.splitext(f.filename)[1].lower()
                if ext in ['.cpp', '.zip', '.txt']:
                    arch_n = f.filename
                    arch_r = f"proj_{g.user.id}_{uuid.uuid4().hex[:8]}{ext}"
                    f.save(os.path.join(UPLOAD_PATH, arch_r))

        if 'captura' in request.files:
            fc = request.files['captura']
            if fc and fc.filename:
                import uuid
                ext = os.path.splitext(fc.filename)[1].lower()
                if ext in ['.png', '.jpg', '.jpeg', '.gif']:
                    cap_n = fc.filename
                    cap_r = f"cap_{g.user.id}_{uuid.uuid4().hex[:8]}{ext}"
                    fc.save(os.path.join(UPLOAD_PATH, cap_r))

        guardar_proyecto(g.user.id, tipo, descripcion, arch_n, arch_r, cap_n, cap_r)
        flash('Proyecto entregado. El administrador lo revisara pronto.', 'success')
        return redirect(url_for('course.certificado'))

    proy = obtener_proyecto(g.user.id)
    return render_template('student/proyecto.html', proyecto=proy)

# ── ADMIN PANEL ──────────────────────────────────────────────────
@course_bp.route('/admin')
@login_required
@solo_admin
def admin_panel():
    usuarios = obtener_todos_usuarios()
    conn = __import__('models.database', fromlist=['get_connection']).get_connection()
    proyectos = conn.execute("""
        SELECT pf.*, u.nombre, u.apellido, u.email
        FROM proyecto_final pf JOIN usuarios u ON u.id=pf.usuario_id
        WHERE pf.estado='entregado' ORDER BY pf.fecha_entrega DESC
    """).fetchall()
    conn.close()
    sg = {
        'total':          len(usuarios),
        'activos':        sum(1 for u in usuarios if u['activo']),
        'estudiantes':    sum(1 for u in usuarios if u['rol'] == 'Estudiante'),
        'proyectos_pend': len(proyectos),
    }
    return render_template('admin/panel.html',
                           usuarios=usuarios, stats_global=sg, proyectos=proyectos)

@course_bp.route('/admin/estudiante/<int:uid>')
@login_required
@solo_admin
def admin_estudiante(uid):
    from models.user import User
    est     = User.get_by_id(uid)
    if not est: abort(404)
    modulos, respuestas = obtener_progreso_estudiante(uid)
    stats   = obtener_estadisticas(uid)
    proyecto = obtener_proyecto(uid)
    return render_template('admin/estudiante.html',
                           estudiante=est, modulos=modulos,
                           respuestas=respuestas, stats=stats, proyecto=proyecto)

@course_bp.route('/admin/proyecto/<int:uid>/revisar', methods=['POST'])
@login_required
@solo_admin
def admin_revisar_proyecto(uid):
    estado     = request.form.get('estado', 'aprobado')
    comentario = request.form.get('comentario', '').strip()
    conn = __import__('models.database', fromlist=['get_connection']).get_connection()
    conn.execute(
        'UPDATE proyecto_final SET estado=?, comentario_admin=? WHERE usuario_id=?',
        (estado, comentario, uid)
    )
    conn.commit()
    conn.close()
    flash(f'Proyecto marcado como {estado}.', 'success')
    return redirect(url_for('course.admin_estudiante', uid=uid))

@course_bp.route('/admin/usuario/<int:uid>/toggle', methods=['POST'])
@login_required
@solo_admin
def admin_toggle(uid):
    toggle_usuario_activo(uid)
    return redirect(url_for('course.admin_panel'))

# ── ERRORES ──────────────────────────────────────────────────────
@course_bp.app_errorhandler(403)
def e403(e):
    return render_template('shared/error.html', codigo=403,
                           mensaje='No tienes permiso para acceder a esta pagina.'), 403

@course_bp.app_errorhandler(404)
def e404(e):
    return render_template('shared/error.html', codigo=404,
                           mensaje='La pagina que buscas no existe.'), 404
