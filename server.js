/**
 * cppLearn — Servidor Backend
 * Base de datos: JSON file (lowdb) — SIN compilacion, funciona en Windows
 * Los datos se guardan en: db.json
 */

const express = require('express');
const bcrypt  = require('bcryptjs');
const jwt     = require('jsonwebtoken');
const path    = require('path');
const cors    = require('cors');
const fs      = require('fs');

const app    = express();
const PORT   = 3000;
const SECRET = 'cpplearn_secret_2025';
const DB_FILE = path.join(__dirname, 'db.json');

// ─── MIDDLEWARE ───────────────────────────────────
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ─── BASE DE DATOS (archivo JSON) ─────────────────
// Se crea automaticamente como db.json
function leerDB() {
  if (!fs.existsSync(DB_FILE)) {
    const inicial = { usuarios: [], progreso: [], ejercicios: [] };
    fs.writeFileSync(DB_FILE, JSON.stringify(inicial, null, 2));
    return inicial;
  }
  return JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
}

function guardarDB(data) {
  fs.writeFileSync(DB_FILE, JSON.stringify(data, null, 2));
}

// Inicializar si no existe
leerDB();
console.log('✓ Base de datos inicializada: db.json');

// ─── MIDDLEWARE JWT ────────────────────────────────
function authMiddleware(req, res, next) {
  const header = req.headers['authorization'];
  if (!header) return res.status(401).json({ error: 'Token requerido' });
  const token = header.split(' ')[1];
  try {
    req.user = jwt.verify(token, SECRET);
    next();
  } catch {
    return res.status(401).json({ error: 'Token invalido o expirado' });
  }
}

// ─── UTILIDADES ───────────────────────────────────
function calcularNivel(xp) {
  if (xp >= 5000) return 6;
  if (xp >= 3000) return 5;
  if (xp >= 1500) return 4;
  if (xp >= 700)  return 3;
  if (xp >= 200)  return 2;
  return 1;
}

function generarId() {
  return Date.now() + Math.floor(Math.random() * 1000);
}

// ─── RUTA: REGISTRO ───────────────────────────────
app.post('/api/registro', (req, res) => {
  const { nombre, apellido, email, password } = req.body;

  if (!nombre || !apellido || !email || !password)
    return res.status(400).json({ error: 'Todos los campos son obligatorios' });
  if (password.length < 6)
    return res.status(400).json({ error: 'La contrasena debe tener minimo 6 caracteres' });

  const db = leerDB();

  // Verificar si el correo ya existe
  if (db.usuarios.find(u => u.email === email))
    return res.status(409).json({ error: 'Este correo ya esta registrado' });

  const hash = bcrypt.hashSync(password, 10);
  const id   = generarId();
  const nuevo = {
    id,
    nombre,
    apellido,
    email,
    password: hash,
    xp: 0,
    racha: 0,
    nivel: 1,
    insignias: 0,
    fechaRegistro: new Date().toISOString()
  };

  db.usuarios.push(nuevo);
  guardarDB(db);

  const token = jwt.sign({ id, email }, SECRET, { expiresIn: '7d' });

  res.json({
    ok: true,
    token,
    usuario: { id, nombre, apellido, email, xp: 0, racha: 0, nivel: 1, insignias: 0 }
  });
});

// ─── RUTA: LOGIN ──────────────────────────────────
app.post('/api/login', (req, res) => {
  const { email, password } = req.body;

  if (!email || !password)
    return res.status(400).json({ error: 'Correo y contrasena requeridos' });

  const db = leerDB();
  const usuario = db.usuarios.find(u => u.email === email);

  if (!usuario || !bcrypt.compareSync(password, usuario.password))
    return res.status(401).json({ error: 'Correo o contrasena incorrectos' });

  const token = jwt.sign({ id: usuario.id, email: usuario.email }, SECRET, { expiresIn: '7d' });

  res.json({
    ok: true,
    token,
    usuario: {
      id:        usuario.id,
      nombre:    usuario.nombre,
      apellido:  usuario.apellido,
      email:     usuario.email,
      xp:        usuario.xp,
      racha:     usuario.racha,
      nivel:     usuario.nivel,
      insignias: usuario.insignias
    }
  });
});

// ─── RUTA: PERFIL ─────────────────────────────────
app.get('/api/perfil', authMiddleware, (req, res) => {
  const db = leerDB();
  const u  = db.usuarios.find(u => u.id === req.user.id);
  if (!u) return res.status(404).json({ error: 'Usuario no encontrado' });

  const modulos    = db.progreso.filter(p => p.usuarioId === req.user.id);
  const ejercicios = db.ejercicios.filter(e => e.usuarioId === req.user.id);

  const totalCorrectos   = ejercicios.filter(e => e.correcto).length;
  const totalIncorrectos = ejercicios.filter(e => !e.correcto).length;
  const total            = totalCorrectos + totalIncorrectos;
  const precision        = total > 0 ? Math.round((totalCorrectos / total) * 100) : 0;

  // No enviar la contrasena
  const { password, ...usuarioSinPw } = u;

  res.json({
    ...usuarioSinPw,
    modulos,
    ejercicios,
    precision,
    ejerciciosResueltos: totalCorrectos
  });
});

// ─── RUTA: GUARDAR EJERCICIO ──────────────────────
app.post('/api/ejercicio', authMiddleware, (req, res) => {
  const { ejercicio_id, correcto } = req.body;
  const uid = req.user.id;
  const db  = leerDB();

  // Buscar si ya existe ese ejercicio para este usuario
  const idx = db.ejercicios.findIndex(e => e.usuarioId === uid && e.ejercicioId === ejercicio_id);

  if (idx >= 0) {
    db.ejercicios[idx].correcto  = correcto;
    db.ejercicios[idx].intentos += 1;
    db.ejercicios[idx].fecha     = new Date().toISOString();
  } else {
    db.ejercicios.push({
      id:          generarId(),
      usuarioId:   uid,
      ejercicioId: ejercicio_id,
      correcto,
      intentos:    1,
      fecha:       new Date().toISOString()
    });
  }

  // Dar XP si es correcto
  const uIdx = db.usuarios.findIndex(u => u.id === uid);
  if (uIdx >= 0) {
    if (correcto) db.usuarios[uIdx].xp += 50;
    db.usuarios[uIdx].nivel = calcularNivel(db.usuarios[uIdx].xp);
  }

  guardarDB(db);

  const u = db.usuarios[uIdx];
  res.json({ ok: true, xp: u ? u.xp : 0, nivel: u ? u.nivel : 1 });
});

// ─── RUTA: PROGRESO DE MODULO ─────────────────────
app.post('/api/modulo', authMiddleware, (req, res) => {
  const { modulo_id, porcentaje } = req.body;
  const uid = req.user.id;
  const db  = leerDB();

  const idx = db.progreso.findIndex(p => p.usuarioId === uid && p.moduloId === modulo_id);

  if (idx >= 0) {
    db.progreso[idx].porcentaje  = porcentaje;
    db.progreso[idx].completado  = porcentaje >= 100;
  } else {
    db.progreso.push({
      id:         generarId(),
      usuarioId:  uid,
      moduloId:   modulo_id,
      porcentaje,
      completado: porcentaje >= 100
    });
  }

  guardarDB(db);
  res.json({ ok: true });
});

// Fallback → index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ─── INICIAR ──────────────────────────────────────
app.listen(PORT, () => {
  console.log(`
  ╔══════════════════════════════════════╗
  ║  cppLearn corriendo en localhost     ║
  ║  → http://localhost:${PORT}            ║
  ║  Base de datos: db.json              ║
  ╚══════════════════════════════════════╝
  `);
});
