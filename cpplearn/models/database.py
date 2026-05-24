"""
models/database.py
Manejo directo de SQLite con el modulo sqlite3 de Python.
No requiere SQLAlchemy ni dependencias externas de BD.

Tablas:
  - roles          : Administrador, Estudiante
  - usuarios       : Datos del usuario + relacion con rol
  - modulos        : Contenido del curso (8 modulos)
  - progreso       : Avance por usuario en cada modulo
  - ejercicios     : Ejercicios disponibles por modulo
  - respuestas     : Respuestas del estudiante a ejercicios
"""

import sqlite3
import os
from config.settings import BASE_DIR

DB_PATH = os.path.join(BASE_DIR, 'cpplearn.db')


def get_connection():
    """Retorna una conexion a la base de datos con row_factory para acceder por nombre de columna."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Crea todas las tablas si no existen e inserta datos iniciales.
    Se ejecuta una sola vez al arrancar la aplicacion.
    """
    conn = get_connection()
    cur  = conn.cursor()

    # ── TABLA: roles ──────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL UNIQUE,
            descripcion TEXT
        )
    """)

    # ── TABLA: usuarios ───────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre           TEXT    NOT NULL,
            apellido         TEXT    NOT NULL,
            email            TEXT    NOT NULL UNIQUE,
            password_hash    TEXT    NOT NULL,
            rol_id           INTEGER NOT NULL DEFAULT 2,
            activo           INTEGER NOT NULL DEFAULT 1,
            xp               INTEGER NOT NULL DEFAULT 0,
            racha            INTEGER NOT NULL DEFAULT 0,
            nivel            INTEGER NOT NULL DEFAULT 1,
            fecha_registro   TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (rol_id) REFERENCES roles(id)
        )
    """)

    # ── TABLA: modulos ────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS modulos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            numero      INTEGER NOT NULL UNIQUE,
            titulo      TEXT    NOT NULL,
            descripcion TEXT,
            nivel       TEXT    NOT NULL DEFAULT 'Basico',
            total_lecciones   INTEGER DEFAULT 0,
            total_ejercicios  INTEGER DEFAULT 0,
            activo      INTEGER NOT NULL DEFAULT 1
        )
    """)

    # ── TABLA: lecciones ─────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lecciones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo_id   INTEGER NOT NULL,
            numero      INTEGER NOT NULL,
            titulo      TEXT    NOT NULL,
            contenido   TEXT,
            FOREIGN KEY (modulo_id) REFERENCES modulos(id)
        )
    """)

    # ── TABLA: ejercicios ─────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ejercicios (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo_id    INTEGER NOT NULL,
            numero       INTEGER NOT NULL,
            titulo       TEXT    NOT NULL,
            descripcion  TEXT,
            codigo_base  TEXT,
            respuesta    TEXT    NOT NULL,
            pista        TEXT,
            dificultad   TEXT    NOT NULL DEFAULT 'Basico',
            FOREIGN KEY (modulo_id) REFERENCES modulos(id)
        )
    """)

    # ── TABLA: progreso ───────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progreso (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id   INTEGER NOT NULL,
            modulo_id    INTEGER NOT NULL,
            porcentaje   INTEGER NOT NULL DEFAULT 0,
            completado   INTEGER NOT NULL DEFAULT 0,
            UNIQUE(usuario_id, modulo_id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (modulo_id)  REFERENCES modulos(id)
        )
    """)

    # ── TABLA: respuestas ─────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS respuestas (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id   INTEGER NOT NULL,
            ejercicio_id INTEGER NOT NULL,
            correcto     INTEGER NOT NULL DEFAULT 0,
            intentos     INTEGER NOT NULL DEFAULT 1,
            fecha        TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(usuario_id, ejercicio_id),
            FOREIGN KEY (usuario_id)   REFERENCES usuarios(id),
            FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id)
        )
    """)

    conn.commit()

    # ── DATOS INICIALES ───────────────────────────────────────────
    _seed_roles(cur, conn)
    _seed_modulos(cur, conn)
    _seed_lecciones(cur, conn)
    _seed_ejercicios(cur, conn)
    _seed_admin(cur, conn)

    conn.close()
    print(f"[DB] Base de datos inicializada en: {DB_PATH}")


def _seed_roles(cur, conn):
    roles = [
        (1, 'Administrador', 'Acceso total al sistema'),
        (2, 'Estudiante',    'Acceso al curso y su progreso'),
    ]
    for r in roles:
        cur.execute("INSERT OR IGNORE INTO roles (id, nombre, descripcion) VALUES (?,?,?)", r)
    conn.commit()


def _seed_modulos(cur, conn):
    modulos = [
        (1, 'Introduccion a C++',       'Historia del lenguaje, entorno de desarrollo, primer programa y estructura basica.',          'Basico',      8, 12),
        (2, 'Variables y Tipos',         'Tipos de datos: int, float, double, char, bool, string. Operadores y conversiones de tipo.', 'Basico',     10, 15),
        (3, 'Estructuras de Control',    'Condicionales if/else/switch. Bucles for, while, do-while. Break y continue.',               'Basico',      9, 14),
        (4, 'Funciones y Recursion',     'Definicion, parametros, retorno, sobrecarga, funciones recursivas y el stack de llamadas.',  'Intermedio', 12, 18),
        (5, 'Arreglos y Matrices',       'Arrays unidimensionales y bidimensionales. Algoritmos de busqueda y ordenamiento basico.',   'Intermedio', 10, 16),
        (6, 'Punteros y Memoria',        'Punteros, referencias, aritmetica de punteros y manejo dinamico con new/delete.',            'Avanzado',   14, 20),
        (7, 'POO — Clases y Objetos',    'Encapsulacion, herencia, polimorfismo, constructores, destructores y operador de acceso.',   'Avanzado',   16, 24),
        (8, 'STL y Plantillas',          'Contenedores vector/map/set, iteradores, algoritmos de la STL y templates basicos.',         'Avanzado',   12, 18),
    ]
    for m in modulos:
        cur.execute("""
            INSERT OR IGNORE INTO modulos (numero, titulo, descripcion, nivel, total_lecciones, total_ejercicios)
            VALUES (?,?,?,?,?,?)
        """, m)
    conn.commit()


def _seed_lecciones(cur, conn):
    # Lecciones del Modulo 1
    lecciones_m1 = [
        (1, 1, 'Historia y filosofia de C++',       '<p>C++ fue creado por <strong>Bjarne Stroustrup</strong> en 1979 como una extension de C con clases. Es un lenguaje de proposito general que ofrece control de bajo nivel junto con abstraccion de alto nivel.</p><p>Se usa en sistemas operativos, videojuegos, motores graficos, bases de datos y aplicaciones de alto rendimiento.</p>'),
        (1, 2, 'Instalacion del entorno',            '<p>Para programar en C++ necesitas un compilador. En Windows puedes usar <strong>MinGW-w64</strong> o instalar <strong>Visual Studio Community</strong>. En Linux el compilador <code>g++</code> generalmente ya esta disponible.</p><p>Un IDE recomendado es <strong>Visual Studio Code</strong> con la extension C/C++.</p>'),
        (1, 3, 'Estructura de un programa C++',     '<p>Todo programa en C++ tiene la funcion <code>main()</code> como punto de entrada. Las directivas <code>#include</code> incorporan librerias. El namespace <code>std</code> contiene las funciones estandar.</p>'),
        (1, 4, 'Hola Mundo y compilacion',          '<p>El programa mas simple en C++ imprime un texto en pantalla usando <code>cout</code>. Para compilar en terminal: <code>g++ -o programa main.cpp</code> y ejecutar con <code>./programa</code>.</p>'),
        (1, 5, 'Entrada y salida estandar',         '<p><code>cout</code> (character output) se usa para imprimir datos. <code>cin</code> (character input) lee datos del usuario. El operador <code>&lt;&lt;</code> envia datos a <code>cout</code> y <code>&gt;&gt;</code> extrae datos de <code>cin</code>.</p>'),
        (1, 6, 'Comentarios y buenas practicas',    '<p>Los comentarios documentan el codigo. Los de una linea usan <code>//</code> y los multilinea usan <code>/* */</code>. Un buen codigo se comenta explicando el <em>por que</em>, no el que.</p>'),
        (1, 7, 'Errores comunes al comenzar',       '<p>Los errores mas frecuentes son: olvidar el punto y coma <code>;</code> al final de cada instruccion, no cerrar llaves <code>{}</code>, usar variables sin declararlas y confundir <code>=</code> (asignacion) con <code>==</code> (comparacion).</p>'),
        (1, 8, 'Ejercicio integrador del modulo 1', '<p>En esta leccion practicas escribir, compilar y ejecutar un programa completo que solicita el nombre del usuario y lo saluda. Aplica todo lo aprendido en el modulo.</p>'),
    ]
    # Lecciones del Modulo 2
    lecciones_m2 = [
        (2, 1,  'Tipos enteros: int, short, long',   '<p>C++ tiene varios tipos enteros. <code>int</code> es el mas comun (4 bytes). <code>short</code> ocupa 2 bytes y <code>long</code> puede ser 4 u 8 bytes segun la plataforma. El prefijo <code>unsigned</code> elimina los valores negativos duplicando el rango positivo.</p>'),
        (2, 2,  'Tipos reales: float y double',      '<p><code>float</code> tiene precision simple (~7 digitos) y ocupa 4 bytes. <code>double</code> tiene precision doble (~15 digitos) y ocupa 8 bytes. Para literales double agrega <code>d</code> o simplemente escribe el punto decimal: <code>3.14</code>.</p>'),
        (2, 3,  'Caracteres y booleanos',            '<p><code>char</code> almacena un caracter ASCII en 1 byte. <code>bool</code> almacena <code>true</code> o <code>false</code> (internamente 1 o 0). Los caracteres se escriben entre comillas simples: <code>\'A\'</code>.</p>'),
        (2, 4,  'Cadenas de texto: string',          '<p>La clase <code>string</code> del header <code>&lt;string&gt;</code> permite trabajar con texto de forma sencilla. Soporta concatenacion con <code>+</code>, acceso por indice con <code>[]</code> y metodos como <code>size()</code>, <code>substr()</code> y <code>find()</code>.</p>'),
        (2, 5,  'Constantes y literales',            '<p>Las constantes se declaran con <code>const</code> y no pueden cambiar su valor. La directiva <code>#define</code> es una alternativa de preprocesador. Las constantes mejoran la legibilidad y evitan errores por valores magicos.</p>'),
        (2, 6,  'Operadores aritmeticos',            '<p>C++ tiene los operadores <code>+</code>, <code>-</code>, <code>*</code>, <code>/</code> y <code>%</code> (modulo). La division entera entre dos <code>int</code> trunca el resultado. Para obtener decimales al menos uno debe ser <code>float</code> o <code>double</code>.</p>'),
        (2, 7,  'Operadores de comparacion',         '<p>Los operadores <code>==</code>, <code>!=</code>, <code>&lt;</code>, <code>&gt;</code>, <code>&lt;=</code>, <code>&gt;=</code> retornan <code>bool</code>. Son la base de las estructuras de control que veras en el modulo 3.</p>'),
        (2, 8,  'Conversion de tipos (casting)',     '<p>C++ convierte tipos automaticamente en algunos casos (conversion implicita). Puedes forzar la conversion con cast: <code>static_cast&lt;double&gt;(entero)</code>. El cast explicito es mas seguro y legible que el estilo C.</p>'),
        (2, 9,  'Overflow y rangos de datos',        '<p>Cada tipo tiene un rango maximo. Si lo superas ocurre un <em>overflow</em> y el valor se envuelve al minimo. Para conocer los limites usa el header <code>&lt;climits&gt;</code> con constantes como <code>INT_MAX</code>.</p>'),
        (2, 10, 'Ejercicio integrador del modulo 2', '<p>Practica declarando variables de distintos tipos, realizando operaciones y mostrando los resultados. Experimenta con casting y observa la diferencia entre division entera y real.</p>'),
    ]

    for lec in lecciones_m1 + lecciones_m2:
        cur.execute("""
            INSERT OR IGNORE INTO lecciones (modulo_id, numero, titulo, contenido)
            VALUES (?,?,?,?)
        """, lec)
    conn.commit()


def _seed_ejercicios(cur, conn):
    ejercicios = [
        # Modulo 1
        (1, 1, 'Hola Mundo',             'Escribe un programa que imprima "Hola, C++" en la pantalla.',                          '#include <iostream>\nusing namespace std;\nint main() {\n    // Tu codigo aqui\n    return 0;\n}',                               'cout',         'Usa cout << para imprimir texto.',         'Basico'),
        (1, 2, 'Saludo personalizado',   'Declara una variable string con tu nombre e imprimela con un saludo.',                  '#include <iostream>\n#include <string>\nusing namespace std;\nint main() {\n    string nombre = ___;\n    cout << "Hola, " << nombre << endl;\n    return 0;\n}', '"C++"',        'Asigna el valor entre comillas dobles.',   'Basico'),
        # Modulo 2
        (2, 1, 'Suma de enteros',        'Declara dos enteros, sumalos y muestra el resultado.',                                  'int a = 10;\nint b = 25;\nint suma = ___;',                                                                                      'a + b',        'El operador de suma es +',                'Basico'),
        (2, 2, 'Division real',          'Divide 7 entre 2 y obtén 3.5 (no 3). Usa el tipo correcto.',                          'double resultado = 7 ___ 2.0;',                                                                                                     '/',            'Usa / con al menos un operando double.',  'Basico'),
        (2, 3, 'Factorial con bucle',    'Calcula el factorial de 5 usando un bucle for.',                                        'int fact = 1;\nfor (int i = 1; i <= 5; i++) {\n    fact ___ i;\n}\ncout << fact;',                                                 '*=',           'Multiplica fact por i en cada iteracion.','Intermedio'),
    ]
    for e in ejercicios:
        cur.execute("""
            INSERT OR IGNORE INTO ejercicios (modulo_id, numero, titulo, descripcion, codigo_base, respuesta, pista, dificultad)
            VALUES (?,?,?,?,?,?,?,?)
        """, e)
    conn.commit()


def _seed_admin(cur, conn):
    """Crea el usuario administrador por defecto si no existe."""
    from werkzeug.security import generate_password_hash
    admin = cur.execute("SELECT id FROM usuarios WHERE email = 'admin@cpplearn.com'").fetchone()
    if not admin:
        cur.execute("""
            INSERT INTO usuarios (nombre, apellido, email, password_hash, rol_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('Admin', 'Sistema', 'admin@cpplearn.com', generate_password_hash('admin123'), 1))
        conn.commit()
        print("[DB] Usuario administrador creado: admin@cpplearn.com / admin123")
