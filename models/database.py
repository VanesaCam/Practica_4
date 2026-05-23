"""
models/database.py — C++ Academy 2026
Base de datos SQLite con restricciones UNIQUE correctas para evitar duplicados.
Lecciones: exactamente 8 por módulo.
Ejercicios: exactamente 3-4 por módulo (bien distribuidos y únicos).
"""
import sqlite3, os
from config.settings import BASE_DIR

DB_PATH    = os.path.join(BASE_DIR, 'cpplearn.db')
UPLOAD_PATH= os.path.join(BASE_DIR, 'static', 'uploads')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    os.makedirs(UPLOAD_PATH, exist_ok=True)
    conn = get_connection()
    c = conn.cursor()
    _crear_tablas(c, conn)
    _seed_roles(c, conn)
    _seed_modulos(c, conn)
    _seed_lecciones(c, conn)
    _seed_ejercicios(c, conn)
    _seed_admin(c, conn)
    conn.close()

def _crear_tablas(c, conn):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS roles(
        id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, descripcion TEXT);

    CREATE TABLE IF NOT EXISTS usuarios(
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre         TEXT NOT NULL,
        apellido        TEXT NOT NULL,
        email           TEXT NOT NULL UNIQUE,
        password_hash   TEXT NOT NULL,
        rol_id          INTEGER NOT NULL DEFAULT 2,
        ruta_aprendizaje TEXT DEFAULT 'desde_cero',
        activo          INTEGER NOT NULL DEFAULT 1,
        xp              INTEGER NOT NULL DEFAULT 0,
        racha           INTEGER NOT NULL DEFAULT 0,
        nivel           INTEGER NOT NULL DEFAULT 1,
        ultimo_modulo   INTEGER DEFAULT NULL,
        ultima_leccion  INTEGER DEFAULT NULL,
        fecha_registro  TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY(rol_id) REFERENCES roles(id));

    CREATE TABLE IF NOT EXISTS modulos(
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        numero           INTEGER NOT NULL UNIQUE,
        titulo           TEXT NOT NULL,
        descripcion      TEXT,
        nivel            TEXT NOT NULL DEFAULT 'Basico',
        total_lecciones  INTEGER DEFAULT 8,
        total_ejercicios INTEGER DEFAULT 3,
        activo           INTEGER NOT NULL DEFAULT 1);

    CREATE TABLE IF NOT EXISTS lecciones(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        modulo_id   INTEGER NOT NULL,
        numero      INTEGER NOT NULL,
        titulo      TEXT NOT NULL,
        contenido   TEXT,
        UNIQUE(modulo_id, numero),
        FOREIGN KEY(modulo_id) REFERENCES modulos(id));

    CREATE TABLE IF NOT EXISTS ejercicios(
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        modulo_id          INTEGER NOT NULL,
        numero             INTEGER NOT NULL,
        titulo             TEXT NOT NULL,
        descripcion        TEXT,
        codigo_base        TEXT,
        opcion_a           TEXT,
        opcion_b           TEXT,
        opcion_c           TEXT,
        opcion_d           TEXT,
        respuesta_correcta TEXT NOT NULL,
        explicacion        TEXT,
        pista              TEXT,
        dificultad         TEXT NOT NULL DEFAULT 'Basico',
        UNIQUE(modulo_id, numero),
        FOREIGN KEY(modulo_id) REFERENCES modulos(id));

    CREATE TABLE IF NOT EXISTS lecciones_completadas(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id  INTEGER NOT NULL,
        leccion_id  INTEGER NOT NULL,
        completada  INTEGER NOT NULL DEFAULT 1,
        fecha       TEXT DEFAULT (datetime('now')),
        UNIQUE(usuario_id, leccion_id),
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY(leccion_id) REFERENCES lecciones(id));

    CREATE TABLE IF NOT EXISTS progreso(
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id  INTEGER NOT NULL,
        modulo_id   INTEGER NOT NULL,
        porcentaje  INTEGER NOT NULL DEFAULT 0,
        completado  INTEGER NOT NULL DEFAULT 0,
        UNIQUE(usuario_id, modulo_id),
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY(modulo_id) REFERENCES modulos(id));

    CREATE TABLE IF NOT EXISTS respuestas(
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id   INTEGER NOT NULL,
        ejercicio_id INTEGER NOT NULL,
        respuesta_dada TEXT,
        correcto     INTEGER NOT NULL DEFAULT 0,
        intentos     INTEGER NOT NULL DEFAULT 1,
        fecha        TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(usuario_id, ejercicio_id),
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
        FOREIGN KEY(ejercicio_id) REFERENCES ejercicios(id));

    CREATE TABLE IF NOT EXISTS proyecto_final(
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id           INTEGER NOT NULL UNIQUE,
        tipo_proyecto        TEXT DEFAULT 'calculadora',
        descripcion_entregada TEXT,
        archivo_nombre       TEXT,
        archivo_ruta         TEXT,
        captura_nombre       TEXT,
        captura_ruta         TEXT,
        estado               TEXT DEFAULT 'pendiente',
        comentario_admin     TEXT,
        fecha_entrega        TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id));
    """)
    conn.commit()

def _seed_roles(c, conn):
    c.execute("INSERT OR IGNORE INTO roles(id,nombre,descripcion) VALUES(1,'Administrador','Acceso total')")
    c.execute("INSERT OR IGNORE INTO roles(id,nombre,descripcion) VALUES(2,'Estudiante','Acceso al curso')")
    conn.commit()

def _seed_modulos(c, conn):
    mods = [
        (1,'Fundamentos de C++',   'Variables, tipos de datos, entrada/salida y compilacion.','Basico',    8,3),
        (2,'Operadores',           'Aritmeticos, logicos, relacionales y expresiones.','Basico',           8,3),
        (3,'Control de Flujo',     'if/else, switch, for, while, do-while, break, continue.','Basico',     8,4),
        (4,'Funciones',            'Definicion, parametros, retorno, sobrecarga, recursion.','Intermedio', 8,3),
        (5,'Introduccion a POO',   'Clases, objetos, atributos, metodos. Los 4 pilares.','Intermedio',     8,3),
        (6,'Clases y Objetos',     'Constructores, destructores, this, sobrecarga de operadores.','Intermedio',8,4),
        (7,'Encapsulamiento',      'public, private, protected. Getters, setters, static.','Avanzado',     8,3),
        (8,'Herencia y Polimorfismo','Herencia, virtual, abstract, override, polimorfismo.','Avanzado',    8,4),
        (9,'Aplicaciones Practicas','Patrones, STL, proyecto final integrador.','Avanzado',               8,3),
    ]
    for m in mods:
        c.execute("""INSERT OR IGNORE INTO modulos(numero,titulo,descripcion,nivel,total_lecciones,total_ejercicios)
                     VALUES(?,?,?,?,?,?)""", m)
    conn.commit()

def _seed_lecciones(c, conn):
    # Exactamente 8 lecciones por módulo, con UNIQUE(modulo_id,numero) no habrá duplicados
    L = [
      # MOD 1 — Fundamentos (8 lecciones)
      (1,1,'Historia: de C a C++',
       '<h3>El lenguaje C++</h3><p><strong>C</strong> fue creado en 1972 por Dennis Ritchie en Bell Labs. <strong>C++</strong> lo creo Bjarne Stroustrup en 1979 como extension orientada a objetos de C.</p>'
       '<h3>Que agrega C++ sobre C</h3><ul><li>Clases y objetos</li><li>Herencia y polimorfismo</li><li>Encapsulamiento</li><li>Manejo de excepciones</li><li>Plantillas (templates)</li></ul>'
       '<div class="info-box">C++ es multiparadigma: puedes programar de forma estructurada (como en C) o de forma orientada a objetos.</div>'),
      (1,2,'Tu primer programa',
       '<h3>Estructura basica</h3><pre class="code-block"><span class="kw">#include</span> <span class="st">&lt;iostream&gt;</span>\n<span class="kw">using namespace</span> <span class="ty">std</span>;\n<span class="ty">int</span> <span class="fn">main</span>() {\n    cout &lt;&lt; <span class="st">"Hola, C++!"</span> &lt;&lt; endl;\n    <span class="kw">return</span> 0;\n}</pre>'
       '<ul><li><code>#include &lt;iostream&gt;</code> — incluye entrada/salida estandar</li><li><code>using namespace std;</code> — permite usar cout sin std::</li><li><code>int main()</code> — punto de entrada obligatorio</li><li><code>return 0;</code> — indica ejecucion exitosa</li></ul>'),
      (1,3,'Variables y Tipos de Datos',
       '<h3>Declarar variables</h3><pre class="code-block"><span class="ty">int</span>    edad    = 20;\n<span class="ty">double</span> precio  = 15.99;\n<span class="ty">char</span>   letra   = \'A\';\n<span class="ty">bool</span>   activo  = <span class="kw">true</span>;\n<span class="ty">string</span> nombre  = <span class="st">"Ana"</span>;</pre>'
       '<table class="data-table"><tr><th>Tipo</th><th>Descripcion</th><th>Ejemplo</th></tr><tr><td>int</td><td>Entero</td><td>10, -5</td></tr><tr><td>double</td><td>Decimal</td><td>3.14</td></tr><tr><td>char</td><td>Un caracter</td><td>\'A\'</td></tr><tr><td>bool</td><td>Verdadero/Falso</td><td>true</td></tr><tr><td>string</td><td>Texto</td><td>"Hola"</td></tr></table>'),
      (1,4,'Entrada y Salida',
       '<h3>cout — imprimir en pantalla</h3><pre class="code-block">cout &lt;&lt; <span class="st">"Nombre: "</span> &lt;&lt; nombre &lt;&lt; endl;\ncout &lt;&lt; <span class="st">"Edad: "</span> &lt;&lt; edad &lt;&lt; <span class="st">" anos"</span> &lt;&lt; endl;</pre>'
       '<h3>cin — leer del usuario</h3><pre class="code-block"><span class="ty">int</span> edad;\ncin &gt;&gt; edad;\n<span class="ty">string</span> nombre;\ncin &gt;&gt; nombre;</pre>'
       '<div class="info-box"><strong>endl</strong> inserta un salto de linea. Equivale a presionar Enter. Tambien puedes usar <code>"\\n"</code>.</div>'),
      (1,5,'Constantes y Comentarios',
       '<h3>Constantes</h3><pre class="code-block"><span class="kw">const</span> <span class="ty">double</span> PI = 3.14159;\n<span class="kw">const</span> <span class="ty">int</span>    MAX = 100;</pre>'
       '<h3>Comentarios</h3><pre class="code-block"><span class="cm">// Comentario de una linea</span>\n<span class="cm">/* Comentario\n   de varias lineas */</span></pre>'
       '<div class="info-box">Las constantes no pueden cambiar su valor durante la ejecucion del programa. Usa nombres en mayusculas por convencion.</div>'),
      (1,6,'Arreglos',
       '<h3>Declarar y usar arreglos</h3><pre class="code-block"><span class="ty">int</span> nums[5] = {10, 20, 30, 40, 50};\ncout &lt;&lt; nums[0]; <span class="cm">// 10 — primer elemento</span>\ncout &lt;&lt; nums[4]; <span class="cm">// 50 — ultimo elemento</span>\n\n<span class="cm">// Recorrer con for:</span>\n<span class="kw">for</span>(<span class="ty">int</span> i = 0; i &lt; 5; i++)\n    cout &lt;&lt; nums[i] &lt;&lt; <span class="st">" "</span>;</pre>'
       '<div class="info-box">Los indices empiezan en 0. Un arreglo de 5 elementos tiene indices 0, 1, 2, 3, 4. Acceder fuera del rango causa comportamiento indefinido.</div>'),
      (1,7,'Cadenas de texto',
       '<h3>La clase string</h3><pre class="code-block"><span class="kw">#include</span> <span class="st">&lt;string&gt;</span>\n<span class="ty">string</span> nombre = <span class="st">"Carlos"</span>;\ncout &lt;&lt; nombre.size();        <span class="cm">// 6</span>\ncout &lt;&lt; nombre.substr(0, 3);  <span class="cm">// "Car"</span>\nnombre += <span class="st">" Lopez"</span>;           <span class="cm">// concatenar</span>\ncout &lt;&lt; nombre;               <span class="cm">// "Carlos Lopez"</span></pre>'
       '<div class="info-box">La clase string de C++ es mucho mas comoda que los char arrays de C. Incluye metodos utiles como size(), substr(), find() y mas.</div>'),
      (1,8,'Compilacion y errores comunes',
       '<h3>Compilar un programa</h3><pre class="code-block"><span class="cm"># Compilar:</span>\ng++ -o mi_programa main.cpp\n<span class="cm"># Ejecutar:</span>\n./mi_programa</pre>'
       '<h3>Errores comunes</h3><ul><li>Olvidar el punto y coma <code>;</code></li><li>Confundir <code>=</code> (asignacion) con <code>==</code> (comparacion)</li><li>Variables no inicializadas</li><li>Acceder fuera del rango de un arreglo</li></ul>'
       '<div class="info-box">C++ es compilado: el codigo se traduce a lenguaje maquina antes de ejecutarse. Los errores de compilacion te dicen exactamente que linea tiene el problema.</div>'),
      # MOD 2 — Operadores (8 lecciones)
      (2,1,'Operadores Aritmeticos',
       '<pre class="code-block"><span class="ty">int</span> a = 10, b = 3;\ncout &lt;&lt; a + b;  <span class="cm">// 13</span>\ncout &lt;&lt; a - b;  <span class="cm">// 7</span>\ncout &lt;&lt; a * b;  <span class="cm">// 30</span>\ncout &lt;&lt; a / b;  <span class="cm">// 3 (division entera)</span>\ncout &lt;&lt; a % b;  <span class="cm">// 1 (resto)</span></pre>'
       '<div class="info-box">La division entre dos <code>int</code> siempre da un resultado entero (truncado). Para obtener decimales, al menos uno debe ser <code>double</code>.</div>'),
      (2,2,'Operadores de Comparacion',
       '<p>Los operadores de comparacion retornan <code>true</code> o <code>false</code>.</p>'
       '<pre class="code-block">x == 5   <span class="cm">// igual</span>\nx != 3   <span class="cm">// diferente</span>\nx &gt;  3   <span class="cm">// mayor que</span>\nx &lt;  10  <span class="cm">// menor que</span>\nx &gt;= 5   <span class="cm">// mayor o igual</span>\nx &lt;= 4   <span class="cm">// menor o igual</span></pre>'),
      (2,3,'Operadores Logicos',
       '<pre class="code-block">a &amp;&amp; b   <span class="cm">// AND — verdadero si ambos son true</span>\na || b   <span class="cm">// OR  — verdadero si al menos uno es true</span>\n!a       <span class="cm">// NOT — invierte el valor booleano</span></pre>'
       '<h3>Tabla de verdad AND</h3><table class="data-table"><tr><th>A</th><th>B</th><th>A && B</th></tr><tr><td>true</td><td>true</td><td>true</td></tr><tr><td>true</td><td>false</td><td>false</td></tr><tr><td>false</td><td>false</td><td>false</td></tr></table>'),
      (2,4,'Asignacion Compuesta e Incremento',
       '<pre class="code-block">x += 5;  <span class="cm">// x = x + 5</span>\nx -= 3;  <span class="cm">// x = x - 3</span>\nx *= 2;  <span class="cm">// x = x * 2</span>\nx /= 4;  <span class="cm">// x = x / 4</span>\nx++;     <span class="cm">// x = x + 1 (post-incremento)</span>\n++x;     <span class="cm">// incrementa antes de usar</span>\nx--;     <span class="cm">// x = x - 1</span></pre>'),
      (2,5,'Precedencia de Operadores',
       '<h3>Orden de evaluacion</h3><pre class="code-block"><span class="ty">int</span> r = 2 + 3 * 4;    <span class="cm">// 14, no 20</span>\n<span class="ty">int</span> s = (2 + 3) * 4; <span class="cm">// 20</span></pre>'
       '<div class="info-box">La precedencia en C++ sigue reglas similares a las matematicas: primero multiplicacion/division, luego suma/resta. Usa parentesis cuando haya duda.</div>'),
      (2,6,'Operador Ternario',
       '<h3>Alternativa compacta al if-else</h3><pre class="code-block"><span class="cm">// condicion ? valor_si_true : valor_si_false</span>\n<span class="ty">int</span> max = (a &gt; b) ? a : b;\n<span class="ty">string</span> estado = (nota &gt;= 60) ? <span class="st">"Aprobado"</span> : <span class="st">"Reprobado"</span>;</pre>'
       '<div class="info-box">El operador ternario es util para asignaciones condicionales simples. Para logica compleja, usa if-else para mayor claridad.</div>'),
      (2,7,'Casting de Tipos',
       '<h3>Conversion entre tipos</h3><pre class="code-block"><span class="cm">// Division decimal:</span>\n<span class="ty">double</span> r = <span class="kw">static_cast</span>&lt;<span class="ty">double</span>&gt;(7) / 2; <span class="cm">// 3.5</span>\n\n<span class="cm">// C++ moderno prefiere static_cast:</span>\n<span class="ty">int</span>  n = 3.7;                    <span class="cm">// trunca a 3</span>\n<span class="ty">int</span>  m = <span class="kw">static_cast</span>&lt;<span class="ty">int</span>&gt;(3.7); <span class="cm">// 3 (explicito)</span></pre>'),
      (2,8,'Practica — Operadores',
       '<h3>Ejercicio integrador</h3><pre class="code-block"><span class="cm">// Calcular precio con IVA</span>\n<span class="ty">double</span> precio, iva;\ncin &gt;&gt; precio;\niva = precio * 0.19;\n<span class="ty">double</span> total = precio + iva;\ncout &lt;&lt; <span class="st">"Total con IVA: "</span> &lt;&lt; total &lt;&lt; endl;\n\n<span class="cm">// Verificar si es par</span>\n<span class="ty">int</span> num;\ncin &gt;&gt; num;\ncout &lt;&lt; ((num % 2 == 0) ? <span class="st">"Par"</span> : <span class="st">"Impar"</span>);</pre>'),
      # MOD 3 — Control de Flujo (8 lecciones)
      (3,1,'if / else if / else',
       '<pre class="code-block"><span class="kw">if</span> (nota &gt;= 90) {\n    cout &lt;&lt; <span class="st">"Excelente"</span>;\n} <span class="kw">else if</span> (nota &gt;= 60) {\n    cout &lt;&lt; <span class="st">"Aprobado"</span>;\n} <span class="kw">else</span> {\n    cout &lt;&lt; <span class="st">"Reprobado"</span>;\n}</pre>'
       '<div class="info-box">Solo se ejecuta el bloque de la primera condicion verdadera. Si ninguna es verdadera, se ejecuta el bloque else (si existe).</div>'),
      (3,2,'switch — multiples casos',
       '<pre class="code-block"><span class="kw">switch</span>(dia) {\n    <span class="kw">case</span> 1: cout &lt;&lt; <span class="st">"Lunes"</span>;  <span class="kw">break</span>;\n    <span class="kw">case</span> 2: cout &lt;&lt; <span class="st">"Martes"</span>; <span class="kw">break</span>;\n    <span class="kw">case</span> 3: cout &lt;&lt; <span class="st">"Miercoles"</span>; <span class="kw">break</span>;\n    <span class="kw">default</span>: cout &lt;&lt; <span class="st">"Otro dia"</span>;\n}</pre>'
       '<div class="info-box">Sin <code>break</code> ocurre "fall-through": el codigo continua ejecutandose en el siguiente case. Esto casi siempre es un bug.</div>'),
      (3,3,'Bucle for',
       '<pre class="code-block"><span class="cm">// Contar del 1 al 5:</span>\n<span class="kw">for</span>(<span class="ty">int</span> i = 1; i &lt;= 5; i++) {\n    cout &lt;&lt; i &lt;&lt; <span class="st">" "</span>;\n}\n<span class="cm">// Salida: 1 2 3 4 5</span>\n\n<span class="cm">// Recorrer arreglo:</span>\n<span class="ty">int</span> arr[] = {10, 20, 30};\n<span class="kw">for</span>(<span class="ty">int</span> i = 0; i &lt; 3; i++)\n    cout &lt;&lt; arr[i];</pre>'),
      (3,4,'Bucle while',
       '<pre class="code-block"><span class="ty">int</span> n = 1;\n<span class="kw">while</span>(n &lt;= 5) {\n    cout &lt;&lt; n &lt;&lt; <span class="st">" "</span>;\n    n++; <span class="cm">// sin esto: bucle infinito</span>\n}</pre>'
       '<div class="info-box">Usa <code>while</code> cuando no sabes de antemano cuantas iteraciones necesitas. Usa <code>for</code> cuando tienes un rango definido.</div>'),
      (3,5,'Bucle do-while',
       '<pre class="code-block"><span class="ty">int</span> opcion;\n<span class="kw">do</span> {\n    cout &lt;&lt; <span class="st">"Ingresa 1-5: "</span>;\n    cin &gt;&gt; opcion;\n} <span class="kw">while</span>(opcion &lt; 1 || opcion &gt; 5);\n\ncout &lt;&lt; <span class="st">"Elegiste: "</span> &lt;&lt; opcion;</pre>'
       '<div class="info-box">El do-while garantiza que el cuerpo se ejecuta al menos una vez antes de verificar la condicion. Util para validacion de entrada.</div>'),
      (3,6,'break y continue',
       '<pre class="code-block"><span class="cm">// break: salir del bucle completamente</span>\n<span class="kw">for</span>(<span class="ty">int</span> i = 0; i &lt; 10; i++) {\n    <span class="kw">if</span>(i == 5) <span class="kw">break</span>;\n    cout &lt;&lt; i;  <span class="cm">// imprime 0 1 2 3 4</span>\n}\n\n<span class="cm">// continue: saltar la iteracion actual</span>\n<span class="kw">for</span>(<span class="ty">int</span> i = 0; i &lt; 6; i++) {\n    <span class="kw">if</span>(i == 3) <span class="kw">continue</span>;\n    cout &lt;&lt; i;  <span class="cm">// imprime 0 1 2 4 5</span>\n}</pre>'),
      (3,7,'Bucles anidados',
       '<h3>Tabla de multiplicar</h3><pre class="code-block"><span class="kw">for</span>(<span class="ty">int</span> i = 1; i &lt;= 5; i++) {\n    <span class="kw">for</span>(<span class="ty">int</span> j = 1; j &lt;= 5; j++) {\n        cout &lt;&lt; i*j &lt;&lt; <span class="st">"\\t"</span>;\n    }\n    cout &lt;&lt; endl;\n}</pre>'
       '<div class="info-box">El bucle exterior define las filas; el interior define las columnas. La complejidad es O(n*m).</div>'),
      (3,8,'Practica — Control de flujo',
       '<h3>Ejercicio: Suma de numeros pares</h3><pre class="code-block"><span class="ty">int</span> suma = 0;\n<span class="kw">for</span>(<span class="ty">int</span> i = 1; i &lt;= 100; i++) {\n    <span class="kw">if</span>(i % 2 == 0) suma += i;\n}\ncout &lt;&lt; <span class="st">"Suma pares 1-100: "</span> &lt;&lt; suma;</pre>'
       '<h3>FizzBuzz classico</h3><pre class="code-block"><span class="kw">for</span>(<span class="ty">int</span> i=1;i&lt;=20;i++){\n    <span class="kw">if</span>(i%15==0) cout&lt;&lt;<span class="st">"FizzBuzz"</span>;\n    <span class="kw">else if</span>(i%3==0) cout&lt;&lt;<span class="st">"Fizz"</span>;\n    <span class="kw">else if</span>(i%5==0) cout&lt;&lt;<span class="st">"Buzz"</span>;\n    <span class="kw">else</span> cout&lt;&lt;i;\n    cout&lt;&lt;<span class="st">" "</span>;\n}</pre>'),
      # MOD 4 — Funciones (8 lecciones)
      (4,1,'Que es una funcion',
       '<h3>Reutilizar codigo</h3><pre class="code-block"><span class="ty">void</span> <span class="fn">saludar</span>() {\n    cout &lt;&lt; <span class="st">"Hola!"</span> &lt;&lt; endl;\n}\n<span class="ty">int</span> <span class="fn">main</span>() {\n    <span class="fn">saludar</span>();  <span class="cm">// llamar la funcion</span>\n    <span class="fn">saludar</span>();  <span class="cm">// llamarla de nuevo</span>\n    <span class="kw">return</span> 0;\n}</pre>'
       '<div class="info-box">Una funcion agrupa un bloque de codigo que puede reutilizarse. Evita repetir codigo y facilita el mantenimiento.</div>'),
      (4,2,'Parametros y Retorno',
       '<pre class="code-block"><span class="ty">int</span> <span class="fn">sumar</span>(<span class="ty">int</span> a, <span class="ty">int</span> b) {\n    <span class="kw">return</span> a + b;\n}\n<span class="ty">double</span> <span class="fn">areaCirculo</span>(<span class="ty">double</span> r) {\n    <span class="kw">return</span> 3.14159 * r * r;\n}\n\ncout &lt;&lt; <span class="fn">sumar</span>(3, 4);          <span class="cm">// 7</span>\ncout &lt;&lt; <span class="fn">areaCirculo</span>(5.0);    <span class="cm">// 78.53...</span></pre>'
       '<div class="info-box"><code>void</code> significa que la funcion no retorna nada. Cualquier otro tipo indica el tipo del valor que retorna.</div>'),
      (4,3,'Paso por Valor y Referencia',
       '<pre class="code-block"><span class="ty">void</span> <span class="fn">porValor</span>(<span class="ty">int</span> x) {\n    x = 100;  <span class="cm">// modifica la copia, no el original</span>\n}\n<span class="ty">void</span> <span class="fn">porReferencia</span>(<span class="ty">int</span>&amp; x) {\n    x = 100;  <span class="cm">// modifica el original</span>\n}\n\n<span class="ty">int</span> n = 5;\n<span class="fn">porValor</span>(n);      cout &lt;&lt; n;  <span class="cm">// 5 (sin cambio)</span>\n<span class="fn">porReferencia</span>(n); cout &lt;&lt; n;  <span class="cm">// 100</span></pre>'),
      (4,4,'Sobrecarga de Funciones',
       '<h3>Misma funcion, distintos parametros</h3><pre class="code-block"><span class="ty">int</span>    <span class="fn">area</span>(<span class="ty">int</span> lado)               { <span class="kw">return</span> lado*lado; }\n<span class="ty">double</span> <span class="fn">area</span>(<span class="ty">double</span> base, <span class="ty">double</span> h)  { <span class="kw">return</span> base*h/2; }\n<span class="ty">double</span> <span class="fn">area</span>(<span class="ty">double</span> r)               { <span class="kw">return</span> 3.14*r*r; }\n\ncout &lt;&lt; <span class="fn">area</span>(4);         <span class="cm">// 16 — cuadrado</span>\ncout &lt;&lt; <span class="fn">area</span>(3.0, 5.0); <span class="cm">// 7.5 — triangulo</span></pre>'
       '<div class="info-box">El compilador elige la version correcta segun los tipos de los argumentos.</div>'),
      (4,5,'Recursion',
       '<pre class="code-block"><span class="ty">int</span> <span class="fn">factorial</span>(<span class="ty">int</span> n) {\n    <span class="kw">if</span>(n == 0) <span class="kw">return</span> 1;          <span class="cm">// caso base</span>\n    <span class="kw">return</span> n * <span class="fn">factorial</span>(n - 1);  <span class="cm">// llamada recursiva</span>\n}\n<span class="ty">int</span> <span class="fn">fibonacci</span>(<span class="ty">int</span> n) {\n    <span class="kw">if</span>(n &lt;= 1) <span class="kw">return</span> n;\n    <span class="kw">return</span> <span class="fn">fibonacci</span>(n-1) + <span class="fn">fibonacci</span>(n-2);\n}</pre>'
       '<div class="info-box">Toda funcion recursiva DEBE tener un caso base. Sin el, la funcion se llama infinitamente hasta causar un stack overflow.</div>'),
      (4,6,'Alcance de Variables',
       '<pre class="code-block"><span class="ty">int</span> global = 100;  <span class="cm">// visible en todo el archivo</span>\n\n<span class="ty">void</span> <span class="fn">funcion</span>() {\n    <span class="ty">int</span> local = 5;  <span class="cm">// solo existe dentro de funcion()</span>\n    cout &lt;&lt; global;  <span class="cm">// puede acceder a global</span>\n    cout &lt;&lt; local;\n}\n<span class="cm">// cout &lt;&lt; local; // ERROR: no existe aqui</span></pre>'
       '<div class="info-box">Las variables locales solo existen dentro del bloque donde fueron declaradas. Las variables globales son accesibles desde cualquier funcion.</div>'),
      (4,7,'Funciones con Arreglos',
       '<pre class="code-block"><span class="ty">void</span> <span class="fn">imprimir</span>(<span class="ty">int</span> arr[], <span class="ty">int</span> n) {\n    <span class="kw">for</span>(<span class="ty">int</span> i = 0; i &lt; n; i++)\n        cout &lt;&lt; arr[i] &lt;&lt; <span class="st">" "</span>;\n}\n<span class="ty">int</span> <span class="fn">sumaArreglo</span>(<span class="ty">int</span> arr[], <span class="ty">int</span> n) {\n    <span class="ty">int</span> suma = 0;\n    <span class="kw">for</span>(<span class="ty">int</span> i = 0; i &lt; n; i++) suma += arr[i];\n    <span class="kw">return</span> suma;\n}\n<span class="ty">int</span> nums[] = {1, 2, 3, 4, 5};\n<span class="fn">imprimir</span>(nums, 5);           <span class="cm">// 1 2 3 4 5</span>\ncout &lt;&lt; <span class="fn">sumaArreglo</span>(nums, 5); <span class="cm">// 15</span></pre>'),
      (4,8,'Practica — Funciones',
       '<h3>Calculadora con funciones</h3><pre class="code-block"><span class="ty">double</span> <span class="fn">sumar</span>(<span class="ty">double</span> a, <span class="ty">double</span> b)  { <span class="kw">return</span> a+b; }\n<span class="ty">double</span> <span class="fn">restar</span>(<span class="ty">double</span> a, <span class="ty">double</span> b) { <span class="kw">return</span> a-b; }\n<span class="ty">double</span> <span class="fn">mult</span>(<span class="ty">double</span> a, <span class="ty">double</span> b)   { <span class="kw">return</span> a*b; }\n<span class="ty">double</span> <span class="fn">div</span>(<span class="ty">double</span> a, <span class="ty">double</span> b) {\n    <span class="kw">if</span>(b == 0) { cerr &lt;&lt; <span class="st">"Error: division por cero"</span>; <span class="kw">return</span> 0; }\n    <span class="kw">return</span> a/b;\n}</pre>'),
      # MOD 5 — Intro POO (8 lecciones)
      (5,1,'Que es la POO',
       '<h3>Programacion Orientada a Objetos</h3><p>La POO es un paradigma que organiza el codigo en torno a <strong>objetos</strong> que combinan datos y comportamiento.</p>'
       '<div class="pillar-grid"><div class="pillar"><strong>Encapsulamiento</strong><p>Ocultar los detalles internos. Solo exponer lo necesario.</p></div><div class="pillar"><strong>Herencia</strong><p>Una clase hereda caracteristicas de otra. Reutilizacion de codigo.</p></div><div class="pillar"><strong>Polimorfismo</strong><p>Mismo metodo, distintos comportamientos segun el objeto.</p></div><div class="pillar"><strong>Abstraccion</strong><p>Modelar conceptos del mundo real como objetos en codigo.</p></div></div>'),
      (5,2,'Clases y Objetos',
       '<div class="analogy-box"><p><strong>Analogia:</strong> La clase es el molde o plano de construccion. El objeto es el producto fabricado con ese molde. Puedes crear muchos objetos del mismo tipo.</p></div>'
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Perro</span> {          <span class="cm">// definicion de la clase (molde)</span>\n<span class="kw">public</span>:\n    <span class="ty">string</span> nombre;\n    <span class="ty">int</span>    edad;\n    <span class="ty">void</span> <span class="fn">ladrar</span>() { cout &lt;&lt; <span class="st">"Guau!"</span>; }\n};\n<span class="ty">Perro</span> fido;            <span class="cm">// crear objeto</span>\nfido.nombre = <span class="st">"Fido"</span>;\nfido.<span class="fn">ladrar</span>();</pre>'),
      (5,3,'Atributos y Metodos',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Coche</span> {\n<span class="kw">public</span>:\n    <span class="cm">// Atributos: datos del objeto</span>\n    <span class="ty">string</span> marca;\n    <span class="ty">int</span>    velocidad = 0;\n    <span class="ty">bool</span>   encendido = <span class="kw">false</span>;\n\n    <span class="cm">// Metodos: comportamiento del objeto</span>\n    <span class="ty">void</span> <span class="fn">encender</span>()  { encendido = <span class="kw">true</span>; }\n    <span class="ty">void</span> <span class="fn">acelerar</span>(int delta) { velocidad += delta; }\n    <span class="ty">void</span> <span class="fn">frenar</span>()    { velocidad = 0; }\n};</pre>'),
      (5,4,'Modificadores de Acceso',
       '<table class="data-table"><tr><th>Modificador</th><th>Accesible desde</th></tr><tr><td>public</td><td>Cualquier parte del programa</td></tr><tr><td>private</td><td>Solo desde dentro de la clase</td></tr><tr><td>protected</td><td>La clase y sus subclases</td></tr></table>'
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Persona</span> {\n<span class="kw">private</span>:\n    <span class="ty">int</span> edad;         <span class="cm">// nadie puede acceder directamente</span>\n<span class="kw">public</span>:\n    <span class="ty">string</span> nombre;   <span class="cm">// todos pueden acceder</span>\n    <span class="ty">int</span> <span class="fn">getEdad</span>()  { <span class="kw">return</span> edad; }\n    <span class="ty">void</span> <span class="fn">setEdad</span>(<span class="ty">int</span> e) { <span class="kw">if</span>(e&gt;0) edad=e; }\n};</pre>'),
      (5,5,'Constructores basicos',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Punto</span> {\n<span class="kw">public</span>:\n    <span class="ty">double</span> x, y;\n    <span class="cm">// Constructor por defecto</span>\n    <span class="ty">Punto</span>() : x(0), y(0) {}\n    <span class="cm">// Constructor con parametros</span>\n    <span class="ty">Punto</span>(<span class="ty">double</span> x, <span class="ty">double</span> y) : x(x), y(y) {}\n    <span class="ty">void</span> <span class="fn">mostrar</span>() { cout &lt;&lt; <span class="st">"("</span> &lt;&lt; x &lt;&lt; <span class="st">","</span> &lt;&lt; y &lt;&lt; <span class="st">")"</span>; }\n};\n<span class="ty">Punto</span> p1;          <span class="cm">// (0, 0)</span>\n<span class="ty">Punto</span> p2(3.0, 4.0); <span class="cm">// (3, 4)</span></pre>'),
      (5,6,'Los 4 Pilares en C++',
       '<h3>Ejemplo practico de encapsulamiento</h3><pre class="code-block"><span class="kw">class</span> <span class="ty">CuentaBancaria</span> {\n<span class="kw">private</span>:\n    <span class="ty">double</span> saldo;    <span class="cm">// encapsulado</span>\n<span class="kw">public</span>:\n    <span class="ty">CuentaBancaria</span>(<span class="ty">double</span> s) : saldo(s) {}\n    <span class="ty">bool</span> <span class="fn">depositar</span>(<span class="ty">double</span> m) {\n        <span class="kw">if</span>(m &lt;= 0) <span class="kw">return false</span>;\n        saldo += m; <span class="kw">return true</span>;\n    }\n    <span class="ty">bool</span> <span class="fn">retirar</span>(<span class="ty">double</span> m) {\n        <span class="kw">if</span>(m &gt; saldo) <span class="kw">return false</span>;\n        saldo -= m; <span class="kw">return true</span>;\n    }\n    <span class="ty">double</span> <span class="fn">getSaldo</span>() { <span class="kw">return</span> saldo; }\n};</pre>'),
      (5,7,'Objetos como parametros',
       '<pre class="code-block"><span class="ty">double</span> <span class="fn">distancia</span>(<span class="ty">Punto</span> a, <span class="ty">Punto</span> b) {\n    <span class="ty">double</span> dx = a.x - b.x;\n    <span class="ty">double</span> dy = a.y - b.y;\n    <span class="kw">return</span> sqrt(dx*dx + dy*dy);\n}\n<span class="ty">Punto</span> p1(0, 0), p2(3, 4);\ncout &lt;&lt; <span class="fn">distancia</span>(p1, p2);  <span class="cm">// 5.0</span></pre>'
       '<div class="info-box">Puedes pasar objetos como parametros igual que tipos primitivos. Para objetos grandes, usa referencias (<code>&amp;</code>) para evitar copias innecesarias.</div>'),
      (5,8,'Practica — Clase Estudiante',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Estudiante</span> {\n<span class="kw">private</span>:\n    <span class="ty">string</span> nombre;\n    <span class="ty">double</span> notas[3];\n<span class="kw">public</span>:\n    <span class="ty">Estudiante</span>(<span class="ty">string</span> n, <span class="ty">double</span> a, <span class="ty">double</span> b, <span class="ty">double</span> c)\n        : nombre(n) { notas[0]=a; notas[1]=b; notas[2]=c; }\n    <span class="ty">double</span> <span class="fn">promedio</span>() {\n        <span class="kw">return</span> (notas[0]+notas[1]+notas[2]) / 3.0;\n    }\n    <span class="ty">bool</span> <span class="fn">aprobado</span>()  { <span class="kw">return</span> <span class="fn">promedio</span>() &gt;= 60; }\n    <span class="ty">string</span> <span class="fn">getNombre</span>() { <span class="kw">return</span> nombre; }\n};</pre>'),
      # MOD 6 — Clases y Objetos (8 lecciones)
      (6,1,'Constructores en detalle',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Rectangulo</span> {\n<span class="kw">public</span>:\n    <span class="ty">double</span> ancho, alto;\n    <span class="cm">// Constructor por defecto</span>\n    <span class="ty">Rectangulo</span>() : ancho(1), alto(1) {}\n    <span class="cm">// Constructor con parametros</span>\n    <span class="ty">Rectangulo</span>(<span class="ty">double</span> a, <span class="ty">double</span> h) : ancho(a), alto(h) {}\n    <span class="cm">// Constructor de copia</span>\n    <span class="ty">Rectangulo</span>(<span class="kw">const</span> <span class="ty">Rectangulo</span>&amp; otro) : ancho(otro.ancho), alto(otro.alto) {}\n    <span class="ty">double</span> <span class="fn">area</span>() { <span class="kw">return</span> ancho * alto; }\n};</pre>'),
      (6,2,'Destructores',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Archivo</span> {\n<span class="kw">private</span>:\n    <span class="ty">string</span> nombre;\n<span class="kw">public</span>:\n    <span class="ty">Archivo</span>(<span class="ty">string</span> n) : nombre(n) {\n        cout &lt;&lt; <span class="st">"Archivo abierto: "</span> &lt;&lt; nombre &lt;&lt; endl;\n    }\n    ~<span class="ty">Archivo</span>() {  <span class="cm">// destructor — empieza con ~</span>\n        cout &lt;&lt; <span class="st">"Archivo cerrado: "</span> &lt;&lt; nombre &lt;&lt; endl;\n    }\n};</pre>'
       '<div class="info-box">El destructor se llama automaticamente cuando el objeto sale de su alcance o se elimina. Ideal para liberar recursos (memoria, archivos, conexiones).</div>'),
      (6,3,'El puntero this',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Persona</span> {\n<span class="kw">public</span>:\n    <span class="ty">string</span> nombre;\n    <span class="ty">int</span>    edad;\n    <span class="cm">// "this" resuelve el conflicto de nombres</span>\n    <span class="ty">Persona</span>(<span class="ty">string</span> nombre, <span class="ty">int</span> edad) {\n        <span class="kw">this</span>-&gt;nombre = nombre;\n        <span class="kw">this</span>-&gt;edad   = edad;\n    }\n    <span class="cm">// this tambien permite encadenar llamadas</span>\n    <span class="ty">Persona</span>&amp; <span class="fn">setNombre</span>(<span class="ty">string</span> n) { nombre=n; <span class="kw">return</span> *<span class="kw">this</span>; }\n};</pre>'),
      (6,4,'Metodos miembro y operador punto',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Circulo</span> {\n<span class="kw">public</span>:\n    <span class="ty">double</span> radio;\n    <span class="ty">Circulo</span>(<span class="ty">double</span> r) : radio(r) {}\n    <span class="ty">double</span> <span class="fn">area</span>();       <span class="cm">// declaracion</span>\n    <span class="ty">double</span> <span class="fn">perimetro</span>(); <span class="cm">// declaracion</span>\n};\n<span class="cm">// Definicion fuera de la clase con ::</span>\n<span class="ty">double</span> <span class="ty">Circulo</span>::<span class="fn">area</span>()       { <span class="kw">return</span> 3.14159 * radio * radio; }\n<span class="ty">double</span> <span class="ty">Circulo</span>::<span class="fn">perimetro</span>() { <span class="kw">return</span> 2 * 3.14159 * radio; }</pre>'),
      (6,5,'Miembros estaticos',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Contador</span> {\n<span class="kw">private</span>:\n    <span class="kw">static</span> <span class="ty">int</span> total;  <span class="cm">// compartido por TODOS los objetos</span>\n<span class="kw">public</span>:\n    <span class="ty">Contador</span>()  { total++; }\n    ~<span class="ty">Contador</span>() { total--; }\n    <span class="kw">static</span> <span class="ty">int</span> <span class="fn">getTotal</span>() { <span class="kw">return</span> total; }\n};\n<span class="ty">int</span> <span class="ty">Contador</span>::total = 0;  <span class="cm">// inicializar fuera</span></pre>'
       '<div class="info-box">Un miembro <code>static</code> pertenece a la clase, no a cada objeto individual. Todos los objetos comparten el mismo valor.</div>'),
      (6,6,'Sobrecarga de operadores',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Vector2D</span> {\n<span class="kw">public</span>:\n    <span class="ty">double</span> x, y;\n    <span class="ty">Vector2D</span>(<span class="ty">double</span> x, <span class="ty">double</span> y) : x(x), y(y) {}\n    <span class="cm">// Sobrecargar operador +</span>\n    <span class="ty">Vector2D</span> <span class="kw">operator</span>+(<span class="kw">const</span> <span class="ty">Vector2D</span>&amp; v) {\n        <span class="kw">return</span> <span class="ty">Vector2D</span>(x + v.x, y + v.y);\n    }\n};\n<span class="ty">Vector2D</span> a(1, 2), b(3, 4);\n<span class="ty">Vector2D</span> c = a + b;  <span class="cm">// (4, 6)</span></pre>'),
      (6,7,'Arreglos de objetos',
       '<pre class="code-block"><span class="ty">Estudiante</span> clase[30];\n<span class="ty">int</span> n = 3;\nclase[0] = <span class="ty">Estudiante</span>(<span class="st">"Ana"</span>,  80, 75, 90);\nclase[1] = <span class="ty">Estudiante</span>(<span class="st">"Luis"</span>, 55, 60, 70);\nclase[2] = <span class="ty">Estudiante</span>(<span class="st">"Mia"</span>,  95, 88, 92);\n\n<span class="kw">for</span>(<span class="ty">int</span> i = 0; i &lt; n; i++) {\n    cout &lt;&lt; clase[i].<span class="fn">getNombre</span>() &lt;&lt; <span class="st">": "</span>\n         &lt;&lt; (clase[i].<span class="fn">aprobado</span>() ? <span class="st">"Aprobado"</span> : <span class="st">"Reprobado"</span>) &lt;&lt; endl;\n}</pre>'),
      (6,8,'Practica — Sistema de Productos',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Producto</span> {\n<span class="kw">private</span>:\n    <span class="ty">string</span> nombre;\n    <span class="ty">double</span> precio;\n    <span class="ty">int</span>    stock;\n<span class="kw">public</span>:\n    <span class="ty">Producto</span>(<span class="ty">string</span> n, <span class="ty">double</span> p, <span class="ty">int</span> s)\n        : nombre(n), precio(p), stock(s) {}\n    <span class="ty">bool</span>   <span class="fn">vender</span>(<span class="ty">int</span> c) { <span class="kw">if</span>(c&gt;stock)<span class="kw">return false</span>; stock-=c; <span class="kw">return true</span>; }\n    <span class="ty">void</span>   <span class="fn">reabastecer</span>(<span class="ty">int</span> c) { stock+=c; }\n    <span class="ty">string</span> <span class="fn">getNombre</span>() { <span class="kw">return</span> nombre; }\n    <span class="ty">double</span> <span class="fn">getPrecio</span>() { <span class="kw">return</span> precio; }\n    <span class="ty">int</span>    <span class="fn">getStock</span>()  { <span class="kw">return</span> stock; }\n};</pre>'),
      # MOD 7 — Encapsulamiento (8 lecciones)
      (7,1,'Que es el encapsulamiento',
       '<div class="analogy-box"><p><strong>Analogia:</strong> Un cajero automatico encapsula su funcionamiento interno. Tu solo ves los botones y la pantalla. No accedes directamente a los billetes ni al sistema.</p></div>'
       '<p>Encapsulamiento significa <strong>ocultar los detalles de implementacion</strong> y solo exponer una interfaz publica limpia. Previene que el codigo externo corrompa el estado interno.</p>'),
      (7,2,'Getters y Setters',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Temperatura</span> {\n<span class="kw">private</span>:\n    <span class="ty">double</span> grados;\n<span class="kw">public</span>:\n    <span class="ty">double</span> <span class="fn">getGrados</span>() { <span class="kw">return</span> grados; }\n    <span class="ty">void</span>   <span class="fn">setGrados</span>(<span class="ty">double</span> g) {\n        <span class="kw">if</span>(g &lt; -273.15) {  <span class="cm">// validacion!</span>\n            cerr &lt;&lt; <span class="st">"Temperatura invalida"</span>;\n            <span class="kw">return</span>;\n        }\n        grados = g;\n    }\n};</pre>'
       '<div class="info-box">La ventaja del setter es la <strong>validacion</strong>: puedes verificar el valor antes de asignarlo, evitando estados invalidos.</div>'),
      (7,3,'public, private, protected',
       '<table class="data-table"><tr><th>Modificador</th><th>Misma clase</th><th>Clase hija</th><th>Exterior</th></tr><tr><td>public</td><td>Si</td><td>Si</td><td>Si</td></tr><tr><td>protected</td><td>Si</td><td>Si</td><td>No</td></tr><tr><td>private</td><td>Si</td><td>No</td><td>No</td></tr></table>'
       '<div class="info-box"><code>private</code> es la maxima restriccion. Usa <code>protected</code> cuando quieras que las clases hijas puedan acceder pero no el codigo externo.</div>'),
      (7,4,'Interfaz publica limpia',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Motor</span> {\n<span class="kw">private</span>:\n    <span class="ty">int</span>  rpm = 0;\n    <span class="ty">bool</span> encendido = <span class="kw">false</span>;\n    <span class="ty">void</span> <span class="fn">inyectarCombustible</span>() { <span class="cm">/* interno */</span> }\n<span class="kw">public</span>:\n    <span class="cm">// Solo exponemos lo necesario:</span>\n    <span class="ty">void</span> <span class="fn">encender</span>() { encendido = <span class="kw">true</span>; rpm = 800; }\n    <span class="ty">void</span> <span class="fn">apagar</span>()   { encendido = <span class="kw">false</span>; rpm = 0; }\n    <span class="ty">int</span>  <span class="fn">getRPM</span>()   { <span class="kw">return</span> rpm; }\n    <span class="ty">bool</span> <span class="fn">estaOn</span>()  { <span class="kw">return</span> encendido; }\n};</pre>'),
      (7,5,'Miembros const',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Circulo</span> {\n<span class="kw">private</span>:\n    <span class="kw">static constexpr</span> <span class="ty">double</span> PI = 3.14159265;\n    <span class="ty">double</span> radio;\n<span class="kw">public</span>:\n    <span class="ty">Circulo</span>(<span class="ty">double</span> r) : radio(r) {}\n    <span class="ty">double</span> <span class="fn">area</span>()      <span class="kw">const</span> { <span class="kw">return</span> PI*radio*radio; }\n    <span class="ty">double</span> <span class="fn">getRadio</span>()  <span class="kw">const</span> { <span class="kw">return</span> radio; }\n    <span class="ty">void</span>   <span class="fn">setRadio</span>(<span class="ty">double</span> r) { <span class="kw">if</span>(r&gt;0) radio=r; }\n};</pre>'
       '<div class="info-box">Un metodo <code>const</code> promete no modificar el objeto. Documentas la intencion y el compilador lo verifica.</div>'),
      (7,6,'Miembros estaticos y clase',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Banco</span> {\n<span class="kw">private</span>:\n    <span class="kw">static</span> <span class="ty">double</span> tasaInteres;  <span class="cm">// misma para todos</span>\n    <span class="ty">double</span> saldo;\n<span class="kw">public</span>:\n    <span class="ty">Banco</span>(<span class="ty">double</span> s) : saldo(s) {}\n    <span class="kw">static</span> <span class="ty">void</span> <span class="fn">setTasa</span>(<span class="ty">double</span> t) { tasaInteres = t; }\n    <span class="ty">double</span> <span class="fn">calcularInteres</span>() { <span class="kw">return</span> saldo * tasaInteres; }\n};\n<span class="ty">double</span> <span class="ty">Banco</span>::tasaInteres = 0.05;</pre>'),
      (7,7,'Principio de ocultacion en practica',
       '<h3>Clase con encapsulamiento completo</h3><pre class="code-block"><span class="kw">class</span> <span class="ty">Empleado</span> {\n<span class="kw">private</span>:\n    <span class="ty">string</span> nombre;\n    <span class="ty">double</span> salario;\n    <span class="ty">string</span> puesto;\n<span class="kw">public</span>:\n    <span class="ty">Empleado</span>(<span class="ty">string</span> n, <span class="ty">double</span> s, <span class="ty">string</span> p)\n        : nombre(n), salario(s), puesto(p) {}\n    <span class="ty">string</span> <span class="fn">getNombre</span>()  { <span class="kw">return</span> nombre; }\n    <span class="ty">string</span> <span class="fn">getPuesto</span>()  { <span class="kw">return</span> puesto; }\n    <span class="ty">bool</span> <span class="fn">darAumento</span>(<span class="ty">double</span> pct) {\n        <span class="kw">if</span>(pct &lt;= 0 || pct &gt; 100) <span class="kw">return false</span>;\n        salario *= (1 + pct/100); <span class="kw">return true</span>;\n    }\n};</pre>'),
      (7,8,'Practica — Encapsulamiento completo',
       '<h3>Disena una clase completamente encapsulada</h3><pre class="code-block"><span class="kw">class</span> <span class="ty">Inventario</span> {\n<span class="kw">private</span>:\n    <span class="ty">Producto</span> items[100];\n    <span class="ty">int</span>      cantidad = 0;\n<span class="kw">public</span>:\n    <span class="ty">bool</span> <span class="fn">agregar</span>(<span class="ty">Producto</span> p) {\n        <span class="kw">if</span>(cantidad &gt;= 100) <span class="kw">return false</span>;\n        items[cantidad++] = p; <span class="kw">return true</span>;\n    }\n    <span class="ty">int</span>  <span class="fn">getCantidad</span>() <span class="kw">const</span> { <span class="kw">return</span> cantidad; }\n    <span class="ty">Producto</span>&amp; <span class="fn">get</span>(<span class="ty">int</span> i)  { <span class="kw">return</span> items[i]; }\n};</pre>'),
      # MOD 8 — Herencia y Polimorfismo (8 lecciones)
      (8,1,'Herencia en C++',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Animal</span> {          <span class="cm">// clase base</span>\n<span class="kw">public</span>:\n    <span class="ty">string</span> nombre;\n    <span class="ty">void</span> <span class="fn">respirar</span>() { cout &lt;&lt; <span class="st">"respirando..."</span>; }\n};\n<span class="kw">class</span> <span class="ty">Perro</span> : <span class="kw">public</span> <span class="ty">Animal</span> {  <span class="cm">// hereda de Animal</span>\n<span class="kw">public</span>:\n    <span class="ty">void</span> <span class="fn">ladrar</span>() { cout &lt;&lt; <span class="st">"Guau!"</span>; }\n};\n<span class="ty">Perro</span> d;\nd.nombre = <span class="st">"Rex"</span>;\nd.<span class="fn">respirar</span>();  <span class="cm">// heredado</span>\nd.<span class="fn">ladrar</span>();   <span class="cm">// propio</span></pre>'),
      (8,2,'Tipos de herencia y acceso',
       '<table class="data-table"><tr><th>Tipo herencia</th><th>public base</th><th>protected base</th><th>private base</th></tr><tr><td>: public</td><td>public</td><td>protected</td><td>NO accesible</td></tr><tr><td>: protected</td><td>protected</td><td>protected</td><td>NO accesible</td></tr><tr><td>: private</td><td>private</td><td>private</td><td>NO accesible</td></tr></table>'
       '<div class="info-box">En la practica, casi siempre se usa <code>: public</code> para preservar la interfaz publica de la clase base.</div>'),
      (8,3,'Sobreescritura de metodos',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Figura</span> {\n<span class="kw">public</span>:\n    <span class="ty">void</span> <span class="fn">dibujar</span>() { cout &lt;&lt; <span class="st">"Figura generica"</span>; }\n};\n<span class="kw">class</span> <span class="ty">Circulo</span> : <span class="kw">public</span> <span class="ty">Figura</span> {\n<span class="kw">public</span>:\n    <span class="ty">void</span> <span class="fn">dibujar</span>() { cout &lt;&lt; <span class="st">"Circulo"</span>; }  <span class="cm">// sobreescribe</span>\n};\n<span class="ty">Circulo</span> c;\nc.<span class="fn">dibujar</span>();   <span class="cm">// "Circulo" — version del hijo</span></pre>'),
      (8,4,'Funciones virtuales',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Animal</span> {\n<span class="kw">public</span>:\n    <span class="kw">virtual</span> <span class="ty">void</span> <span class="fn">hablar</span>() { cout &lt;&lt; <span class="st">"..."</span>; }\n};\n<span class="kw">class</span> <span class="ty">Perro</span> : <span class="kw">public</span> <span class="ty">Animal</span> {\n<span class="kw">public</span>:\n    <span class="ty">void</span> <span class="fn">hablar</span>() <span class="kw">override</span> { cout &lt;&lt; <span class="st">"Guau"</span>; }\n};\n<span class="ty">Animal</span>* a = <span class="kw">new</span> <span class="ty">Perro</span>();\na-&gt;<span class="fn">hablar</span>();  <span class="cm">// "Guau" — polimorfismo!</span></pre>'
       '<div class="info-box"><code>virtual</code> activa el polimorfismo dinamico. Sin virtual, se llamaria siempre la version de la clase base.</div>'),
      (8,5,'Clases abstractas',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Forma</span> {              <span class="cm">// clase abstracta</span>\n<span class="kw">public</span>:\n    <span class="kw">virtual</span> <span class="ty">double</span> <span class="fn">area</span>()      = 0;  <span class="cm">// virtual puro</span>\n    <span class="kw">virtual</span> <span class="ty">string</span> <span class="fn">nombre</span>()   = 0;\n    <span class="ty">void</span> <span class="fn">info</span>() { cout &lt;&lt; <span class="fn">nombre</span>() &lt;&lt; <span class="st">": "</span> &lt;&lt; <span class="fn">area</span>(); }\n};\n<span class="kw">class</span> <span class="ty">Cuadrado</span> : <span class="kw">public</span> <span class="ty">Forma</span> {\n    <span class="ty">double</span> lado;\n<span class="kw">public</span>:\n    <span class="ty">Cuadrado</span>(<span class="ty">double</span> l) : lado(l) {}\n    <span class="ty">double</span> <span class="fn">area</span>()    <span class="kw">override</span> { <span class="kw">return</span> lado*lado; }\n    <span class="ty">string</span> <span class="fn">nombre</span>() <span class="kw">override</span> { <span class="kw">return</span> <span class="st">"Cuadrado"</span>; }\n};</pre>'),
      (8,6,'Polimorfismo en accion',
       '<pre class="code-block"><span class="ty">Forma</span>* figuras[3];\nfiguras[0] = <span class="kw">new</span> <span class="ty">Cuadrado</span>(4);\nfiguras[1] = <span class="kw">new</span> <span class="ty">Circulo</span>(3);\nfiguras[2] = <span class="kw">new</span> <span class="ty">Triangulo</span>(5, 4);\n\n<span class="kw">for</span>(<span class="ty">int</span> i = 0; i &lt; 3; i++) {\n    figuras[i]-&gt;<span class="fn">info</span>();  <span class="cm">// llama la version correcta</span>\n    cout &lt;&lt; endl;\n}\n<span class="cm">// Cuadrado: 16</span>\n<span class="cm">// Circulo: 28.27</span>\n<span class="cm">// Triangulo: 10</span></pre>'),
      (8,7,'override y final',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Base</span> { <span class="kw">public</span>: <span class="kw">virtual</span> <span class="ty">void</span> <span class="fn">f</span>() {} };\n<span class="kw">class</span> <span class="ty">Der1</span> : <span class="kw">public</span> <span class="ty">Base</span> {\n<span class="kw">public</span>:\n    <span class="ty">void</span> <span class="fn">f</span>() <span class="kw">override</span> {} <span class="cm">// confirma sobreescritura</span>\n};\n<span class="kw">class</span> <span class="ty">Der2</span> : <span class="kw">public</span> <span class="ty">Der1</span> {\n<span class="kw">public</span>:\n    <span class="cm">// void f() override {} // ERROR: Der1 uso final</span>\n};</pre>'
       '<div class="info-box"><code>override</code>: el compilador verifica que realmente sobreescriba una virtual. <code>final</code>: impide que se sobreescriba de nuevo.</div>'),
      (8,8,'Practica — Sistema de Empleados',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Empleado</span> {\n<span class="kw">protected</span>: <span class="ty">string</span> nombre; <span class="ty">double</span> salarioBase;\n<span class="kw">public</span>:\n    <span class="ty">Empleado</span>(<span class="ty">string</span> n, <span class="ty">double</span> s): nombre(n),salarioBase(s){}\n    <span class="kw">virtual</span> <span class="ty">double</span> <span class="fn">salario</span>() = 0;\n    <span class="ty">string</span> <span class="fn">getNombre</span>() { <span class="kw">return</span> nombre; }\n};\n<span class="kw">class</span> <span class="ty">Gerente</span>: <span class="kw">public</span> <span class="ty">Empleado</span>{\n    <span class="ty">double</span> bono;\n<span class="kw">public</span>:\n    <span class="ty">Gerente</span>(<span class="ty">string</span> n,<span class="ty">double</span> s,<span class="ty">double</span> b):Empleado(n,s),bono(b){}\n    <span class="ty">double</span> <span class="fn">salario</span>() <span class="kw">override</span> { <span class="kw">return</span> salarioBase+bono; }\n};</pre>'),
      # MOD 9 — Aplicaciones Practicas (8 lecciones)
      (9,1,'Proyecto: Planificacion',
       '<h3>Tu proyecto final</h3><p>En este modulo pondras en practica todo lo aprendido creando una aplicacion real en C++.</p>'
       '<h3>Opciones de proyecto</h3><ul><li><strong>Calculadora:</strong> operaciones con clases y validacion</li><li><strong>Sistema de estudiantes:</strong> registro y calculo de promedios</li><li><strong>Juego: Adivina el numero</strong> con contador de intentos</li><li><strong>Gestor de tareas:</strong> lista con prioridades</li></ul>'
       '<div class="info-box">Elige el proyecto que mas te motive. Los buenos programadores hacen proyectos que les apasionan.</div>'),
      (9,2,'Herramientas y entorno',
       '<h3>Que instalar</h3><ol><li><strong>Compilador g++</strong> — <a href="https://www.mingw-w64.org/" target="_blank">MinGW-w64</a> para Windows. Selecciona arquitectura x86_64.</li><li><strong>Editor</strong> — <a href="https://code.visualstudio.com/" target="_blank">Visual Studio Code</a> con la extension C/C++ de Microsoft.</li></ol>'
       '<pre class="code-block"><span class="cm"># Verificar instalacion (en CMD):</span>\ng++ --version\n<span class="cm"># Resultado esperado: g++ (MinGW...) 13.x.x</span></pre>'
       '<div class="info-box">Tambien puedes usar Dev-C++, Code::Blocks o CLion si ya los tienes instalados.</div>'),
      (9,3,'Estructura base del proyecto',
       '<pre class="code-block"><span class="cm">// mi_proyecto.cpp</span>\n<span class="kw">#include</span> <span class="st">&lt;iostream&gt;</span>\n<span class="kw">#include</span> <span class="st">&lt;string&gt;</span>\n<span class="kw">using namespace</span> <span class="ty">std</span>;\n\n<span class="kw">class</span> <span class="ty">MiApp</span> {\n<span class="kw">private</span>:\n    <span class="ty">string</span> nombre;\n<span class="kw">public</span>:\n    <span class="ty">MiApp</span>(<span class="ty">string</span> n) : nombre(n) {}\n    <span class="ty">void</span> <span class="fn">mostrarMenu</span>() {\n        cout &lt;&lt; <span class="st">"=== "</span> &lt;&lt; nombre &lt;&lt; <span class="st">" ==="</span> &lt;&lt; endl;\n        cout &lt;&lt; <span class="st">"1. Opcion 1"</span> &lt;&lt; endl;\n        cout &lt;&lt; <span class="st">"0. Salir"</span> &lt;&lt; endl;\n    }\n    <span class="ty">void</span> <span class="fn">ejecutar</span>() {\n        <span class="ty">int</span> op;\n        <span class="kw">do</span> { <span class="fn">mostrarMenu</span>(); cin &gt;&gt; op; } <span class="kw">while</span>(op != 0);\n    }\n};\n\n<span class="ty">int</span> <span class="fn">main</span>() {\n    <span class="ty">MiApp</span> app(<span class="st">"Mi Aplicacion C++"</span>);\n    app.<span class="fn">ejecutar</span>();\n    <span class="kw">return</span> 0;\n}</pre>'),
      (9,4,'Ejemplo: Calculadora completa',
       '<pre class="code-block"><span class="kw">class</span> <span class="ty">Calculadora</span> {\n<span class="kw">private</span>:\n    <span class="ty">double</span> resultado = 0;\n<span class="kw">public</span>:\n    <span class="ty">void</span> <span class="fn">sumar</span>(<span class="ty">double</span> a, <span class="ty">double</span> b) {\n        resultado = a + b;\n        cout &lt;&lt; a &lt;&lt; <span class="st">" + "</span> &lt;&lt; b &lt;&lt; <span class="st">" = "</span> &lt;&lt; resultado &lt;&lt; endl;\n    }\n    <span class="ty">void</span> <span class="fn">dividir</span>(<span class="ty">double</span> a, <span class="ty">double</span> b) {\n        <span class="kw">if</span>(b == 0) { cerr &lt;&lt; <span class="st">"Error: division por cero"</span>; <span class="kw">return</span>; }\n        resultado = a / b;\n        cout &lt;&lt; a &lt;&lt; <span class="st">" / "</span> &lt;&lt; b &lt;&lt; <span class="st">" = "</span> &lt;&lt; resultado &lt;&lt; endl;\n    }\n    <span class="ty">double</span> <span class="fn">getResultado</span>() { <span class="kw">return</span> resultado; }\n};</pre>'),
      (9,5,'Compilar y ejecutar',
       '<h3>Pasos de compilacion</h3><pre class="code-block"><span class="cm"># 1. Compilar:</span>\ng++ -o mi_proyecto mi_proyecto.cpp\n\n<span class="cm"># 2. Ejecutar (Windows):</span>\nmi_proyecto.exe\n\n<span class="cm"># 2. Ejecutar (Linux/Mac):</span>\n./mi_proyecto\n\n<span class="cm"># Compilar con avisos:</span>\ng++ -Wall -Wextra -o mi_proyecto mi_proyecto.cpp</pre>'
       '<div class="info-box"><code>-Wall</code> activa todos los avisos del compilador. Es buena practica usarlo siempre: te ayuda a detectar errores antes de que causen problemas.</div>'),
      (9,6,'STL — vector y map',
       '<h3>Contenedores de la libreria estandar</h3><pre class="code-block"><span class="kw">#include</span> <span class="st">&lt;vector&gt;</span>\n<span class="kw">#include</span> <span class="st">&lt;map&gt;</span>\n\n<span class="ty">vector</span>&lt;<span class="ty">int</span>&gt; nums = {1, 2, 3, 4, 5};\nnums.<span class="fn">push_back</span>(6);\n<span class="kw">for</span>(<span class="ty">auto</span> n : nums) cout &lt;&lt; n &lt;&lt; <span class="st">" "</span>;\n\n<span class="ty">map</span>&lt;<span class="ty">string</span>, <span class="ty">int</span>&gt; edades;\nedades[<span class="st">"Ana"</span>]  = 20;\nedades[<span class="st">"Luis"</span>] = 22;\ncout &lt;&lt; edades[<span class="st">"Ana"</span>];  <span class="cm">// 20</span></pre>'),
      (9,7,'Buenas practicas',
       '<h3>Escribe codigo profesional</h3><ul><li><strong>Nombres descriptivos:</strong> <code>calcularPromedio()</code> en lugar de <code>cp()</code></li><li><strong>Una responsabilidad por clase (SRP)</strong></li><li><strong>Usa <code>const</code></strong> en metodos que no modifican el objeto</li><li><strong>Declara <code>override</code></strong> explicitamente al sobreescribir</li><li><strong>Prefiere <code>nullptr</code></strong> sobre <code>NULL</code> o <code>0</code></li><li><strong>Libera la memoria</strong> con <code>delete</code> cuando uses <code>new</code></li></ul>'
       '<div class="info-box">El codigo limpio se escribe para las personas que lo leeran despues — incluyendo tu yo del futuro.</div>'),
      (9,8,'Entrega del proyecto',
       '<h3>Como entregar tu proyecto</h3><ol><li>Escribe tu codigo en un archivo <code>mi_proyecto.cpp</code></li><li>Compilalo: <code>g++ -o mi_proyecto mi_proyecto.cpp</code></li><li>Ejecutalo y verifica que funciona correctamente</li><li>Toma una captura de pantalla del resultado en la consola</li><li>Sube tu archivo .cpp y la captura en la seccion de Proyecto Final</li></ol>'
       '<div class="info-box">Al entregar tu proyecto y completar todos los modulos de tu nivel, se genera tu certificado oficial de C++ Academy 2026.</div>'),
    ]
    for l in L:
        c.execute("INSERT OR IGNORE INTO lecciones(modulo_id,numero,titulo,contenido) VALUES(?,?,?,?)", l)
    conn.commit()

def _seed_ejercicios(c, conn):
    import random
    random.seed(42)
    def mk(mod, num, tit, desc, cod, correcta, incorrectas, expl, pista, dif):
        lec = c.execute("SELECT id FROM lecciones WHERE modulo_id=? ORDER BY numero LIMIT 1 OFFSET ?", (mod, num-1)).fetchone()
        opts = [correcta] + list(incorrectas)
        random.shuffle(opts)
        letra = chr(ord('a') + opts.index(correcta))
        return (mod, num, tit, desc, cod, opts[0], opts[1], opts[2], opts[3], letra, expl, pista, dif)

    EJS = [
        mk(1,1,'Tipo para decimales','¿Que tipo de dato almacena el numero 3.14 en C++?',None,
           'double',['int','char','bool'],
           'double almacena numeros decimales de doble precision. int solo guarda enteros. char almacena un caracter. bool es true/false.','Piensa en que tipo necesitas para guardar decimales.','Basico'),
        mk(1,2,'Instruccion de salida','¿Como se imprime texto en pantalla en C++?',None,
           'cout <<',['printf()','print()','System.out'],
           'cout con el operador << es la salida estandar de C++. printf() es de C pero funciona. print() es Python. System.out es Java.','Objeto de salida estandar de C++ con operador <<.','Basico'),
        mk(1,3,'Funcion de entrada','¿Como se llama la funcion obligatoria de todo programa C++?',None,
           'main()',['inicio()','start()','begin()'],
           'main() es el punto de entrada definido por el estandar C++. inicio(), start() y begin() no existen como punto de entrada en C++.','Es el punto de inicio de todo programa.','Basico'),
        mk(2,1,'Division entera','Si a=7 y b=2 son int, ¿que retorna a/b?',None,
           '3',['3.5','4','Error de compilacion'],
           'La division entre dos int trunca el decimal. 7/2 matematicamente es 3.5, pero como ambos son int el resultado es 3. Para 3.5 uno debe ser double.','La division entre enteros trunca el resultado.','Basico'),
        mk(2,2,'Operador modulo','¿Que retorna la expresion 10 % 3?',None,
           '1',['3','0','3.33'],
           '% retorna el RESTO de la division entera. 10 dividido 3 da cociente 3 y RESTO 1. No retorna el cociente ni el resultado exacto.','% da el resto, no el cociente.','Basico'),
        mk(2,3,'Asignacion compuesta','Si x=5, ¿que valor tiene x despues de ejecutar x+=3?',None,
           '8',['3','5','15'],
           'x+=3 equivale a x = x + 3 = 5 + 3 = 8. No es solo el incremento (3), ni el original (5), ni 15 (que seria multiplicacion x*=3).','El operador += suma el valor actual mas el numero dado.','Basico'),
        mk(3,1,'Resultado de condicional','nota=45. ¿Que imprime: if(nota>=60) cout<<"Aprobado"; else cout<<"Reprobado";?',None,
           'Reprobado',['Aprobado','No imprime nada','Error de ejecucion'],
           '45 no cumple la condicion >=60 (es false), por tanto se ejecuta el else: imprime Reprobado. Si nota fuera 60 o mas, imprimiria Aprobado.','Evalua si 45 cumple la condicion mayor o igual a 60.','Basico'),
        mk(3,2,'Iteraciones del for','¿Cuantas veces se ejecuta: for(int i=0; i<5; i++)?',None,
           '5 veces',['4 veces','6 veces','Infinitas'],
           'i toma los valores 0,1,2,3,4. Cuando i llega a 5 la condicion i<5 es false y el bucle termina. Son exactamente 5 iteraciones.','Cuenta los valores de i: empieza en 0, termina antes de 5.','Basico'),
        mk(3,3,'Funcion de break','¿Para que sirve break dentro de un bucle?',None,
           'Termina el bucle completamente',['Pausa el bucle 1 segundo','Salta a la siguiente iteracion','Reinicia el contador del bucle'],
           'break termina el bucle por completo. No existe pausa en C++. continue salta la iteracion actual. No reinicia contadores.','break = romper el bucle y salir.','Basico'),
        mk(3,4,'Fall-through en switch','¿Que ocurre si olvidas break en un case de switch?',None,
           'El codigo continua ejecutandose en el siguiente case',['Error de compilacion','Se ignora ese case','El programa termina'],
           'Sin break ocurre "fall-through": el codigo cae al siguiente case y lo ejecuta aunque no coincida. Casi siempre es un bug.','El codigo cae al siguiente case sin detenerse.','Intermedio'),
        mk(4,1,'Tipo de retorno void','¿Que significa void como tipo de retorno de una funcion?',None,
           'La funcion no retorna ningun valor',['Retorna el numero cero','Retorna una cadena vacia','Es el tipo de retorno obligatorio'],
           'void indica explicitamente que la funcion no devuelve nada. Retornar 0 requiere int. Retornar cadena requiere string. No es obligatorio.','void = vacio, sin valor de retorno.','Basico'),
        mk(4,2,'Caso base recursivo','¿Por que es obligatorio el caso base en recursion?',None,
           'Para detener las llamadas y evitar desbordamiento del stack',['Para hacer la funcion mas rapida','Para ahorrar memoria RAM','Para que pueda llamarse desde main'],
           'Sin caso base la funcion se llama indefinidamente hasta agotar la memoria del stack (stack overflow). No tiene relacion con velocidad ni con como se invoca.','Sin caso base la recursion no se detiene.','Intermedio'),
        mk(4,3,'Paso por referencia','¿Como declaras un parametro para modificar la variable original?',None,
           'void f(int &x)',['void f(int x)','void f(int *x)','void f(const int x)'],
           'El operador & crea una referencia: el parametro es un alias del original. int x es una copia (no modifica). int *x es puntero (diferente). const impide modificar.','El simbolo & despues del tipo crea una referencia.','Intermedio'),
        mk(5,1,'Los 4 pilares','¿Cuales son los 4 pilares de la Programacion Orientada a Objetos?',None,
           'Encapsulamiento, Herencia, Polimorfismo, Abstraccion',
           ['Variables, Funciones, Bucles, Clases','Compilacion, Ejecucion, Debug, Testing','Clases, Metodos, Atributos, Constructores'],
           'Los 4 pilares son E-H-P-A: Encapsulamiento (ocultar datos), Herencia (reutilizar), Polimorfismo (misma interfaz distintos comportamientos) y Abstraccion (modelar el mundo real).','Recuerda la sigla E-H-P-A.','Basico'),
        mk(5,2,'Clase vs Objeto','¿Cual es la relacion correcta entre clase y objeto?',None,
           'El objeto es una instancia creada a partir de la clase',['Son exactamente lo mismo','La clase hereda del objeto','El objeto define como se crea la clase'],
           'La clase es el molde o plano. El objeto es el producto concreto creado con ese molde. Puedes crear muchos objetos distintos de la misma clase.','Clase = molde, objeto = producto fabricado.','Basico'),
        mk(5,3,'Operador de acceso','¿Que operador accede a miembros de un objeto normal en C++?',None,
           '. (punto)',['-> (flecha)',':: (doble dos puntos)','* (asterisco)'],
           'El punto (.) accede a miembros de un objeto declarado normalmente. La flecha (->) se usa con punteros a objetos. :: es el operador de resolucion de alcance. * desreferencia punteros.','Objeto normal = punto. Puntero a objeto = flecha.','Basico'),
        mk(6,1,'Constructor en C++','¿Que caracteriza a un constructor?',None,
           'Tiene el mismo nombre que la clase y no tiene tipo de retorno',['Tiene tipo de retorno int','Se llama al destruir el objeto','Solo puede tener un parametro'],
           'El constructor tiene nombre identico a la clase y NO tiene tipo de retorno (ni siquiera void). Se ejecuta al crear el objeto. El destructor se llama al destruir. Puede tener cualquier numero de parametros.','Constructor = nombre de la clase, sin tipo de retorno.','Basico'),
        mk(6,2,'Identificador del destructor','¿Como se identifica un destructor en C++?',None,
           '~ seguido del nombre de la clase, sin parametros',['del + nombre','Tipo de retorno bool','Puede tener parametros opcionales'],
           'El destructor siempre es ~NombreClase() sin parametros ni tipo de retorno. La tilde ~ es su identificador unico. del es Python. bool no es valido. No puede tener parametros.','Tilde (~) seguido del nombre de la clase.','Basico'),
        mk(6,3,'Puntero this','¿Para que sirve el puntero this en C++?',None,
           'Referencia al objeto actual dentro de sus propios metodos',['Para crear un nuevo objeto','Para acceder a la clase padre','Para destruir el objeto actual'],
           'this apunta al objeto que esta ejecutando el metodo en ese momento. Es util cuando un parametro tiene el mismo nombre que un atributo: this->nombre = nombre. No crea objetos ni destruye ni referencia al padre.','this = este objeto actual en este momento.','Intermedio'),
        mk(6,4,'Miembro static','¿Que caracteriza a un miembro static de una clase?',None,
           'Es compartido por todos los objetos de la clase',['Solo existe durante la ejecucion','Es privado por defecto','No se puede modificar despues de crearlo'],
           'Un miembro static pertenece a LA CLASE, no a cada objeto individual. Todos los objetos comparten el mismo valor. No tiene relacion con modificadores de acceso ni con const.','static = uno para todos los objetos.','Intermedio'),
        mk(7,1,'Acceso private','¿Desde donde se puede acceder a un miembro declarado private?',None,
           'Solo desde dentro de la misma clase',['Desde cualquier parte del programa','Desde clases hijas con herencia','Solo desde la funcion main'],
           'private es la maxima restriccion: solo los metodos de esa misma clase pueden acceder. Las clases hijas necesitan protected. El codigo externo no puede acceder bajo ninguna circunstancia.','private = solo yo (la misma clase) me veo.','Basico'),
        mk(7,2,'Ventaja del setter','¿Cual es la principal ventaja de un setter sobre acceso directo al atributo?',None,
           'Permite validar el valor antes de asignarlo',['Los setters son mas rapidos','Son obligatorios para todo atributo privado','Hacen el atributo accesible publicamente'],
           'La ventaja real es la validacion: el setter puede verificar que el valor sea valido antes de asignarlo (por ejemplo, que edad no sea negativa). El acceso directo no permite esto.','Setter = portero que valida antes de dejar pasar.','Basico'),
        mk(7,3,'Metodo const','¿Que garantiza declarar un metodo como const?',None,
           'Que el metodo no modificara el estado del objeto',['Que es mas rapido','Que no puede heredarse','Que es obligatorio declararlo'],
           'Un metodo const promete no modificar el objeto. El compilador lo verifica y rechaza cualquier asignacion a miembros. Ademas permite llamarlo desde objetos constantes.','const al final = promesa de no modificar.','Intermedio'),
        mk(8,1,'Sintaxis de herencia','¿Como hereda la clase Perro de Animal en C++?',None,
           'class Perro : public Animal {}',['class Perro extends Animal {}','class Perro inherits Animal {}','class Perro(Animal) {}'],
           'En C++ la herencia usa dos puntos (:) seguidos del tipo de acceso y la clase base. extends es Java/JavaScript. inherits no existe en C++. La sintaxis con parentesis es Python.','Dos puntos (:) + public + nombre de la clase base.','Basico'),
        mk(8,2,'Funcion virtual','¿Para que sirve la palabra clave virtual?',None,
           'Para activar el polimorfismo dinamico con punteros a clase base',['Para hacer la funcion mas rapida','Para declarar una funcion sin implementacion','Para impedir que la funcion sea sobreescrita'],
           'virtual activa el polimorfismo dinamico: cuando tienes un puntero a clase base, C++ llama la version correcta segun el tipo real del objeto. Para funcion sin implementacion necesitas = 0.','virtual = C++ decide en tiempo de ejecucion cual version llamar.','Intermedio'),
        mk(8,3,'Clase abstracta','¿Que hace a una clase abstracta en C++?',None,
           'Tener al menos un metodo virtual puro (= 0)',['Todos sus atributos son private','No tener constructor definido','Heredar de mas de dos clases'],
           'Una clase es abstracta cuando tiene al menos un metodo virtual puro (= 0). No puedes crear objetos directamente de ella. Tener atributos private es encapsulamiento normal.','virtual tipo nombre() = 0; es el metodo virtual puro.','Intermedio'),
        mk(8,4,'Polimorfismo','¿Que permite el polimorfismo en POO?',None,
           'Que objetos de distintas clases respondan al mismo mensaje de forma diferente',['Crear copias identicas de una clase','Acceder a atributos privados','Impedir que una clase sea heredada'],
           'Polimorfismo permite que el mismo metodo tenga comportamientos distintos segun el tipo real del objeto. Es la base del diseno orientado a objetos flexible.','Mismo metodo, distintos comportamientos segun el objeto.','Intermedio'),
        mk(9,1,'Principio SRP','¿Que establece el principio de responsabilidad unica (SRP)?',None,
           'Cada clase debe tener una sola razon para cambiar',['Una clase debe hacer todo lo posible','Solo puede tener un metodo','No puede tener mas de diez atributos'],
           'SRP dice que cada clase debe tener UNA sola responsabilidad. Si una clase cambia por dos razones distintas, debe dividirse en dos clases. El numero de metodos o atributos no define el SRP.','Una clase = una tarea bien definida.','Avanzado'),
        mk(9,2,'Keyword override','¿Para que sirve override en C++ moderno?',None,
           'Para indicar explicitamente que se sobreescribe una funcion virtual del padre',['Para crear una nueva funcion normal','Para impedir que se sobreescriba','Para llamar automaticamente al metodo del padre'],
           'override le dice al compilador tu intencion de sobreescribir. Si el metodo no existe en la clase base o la firma no coincide, el compilador da error. Sin override ese error pasaria desapercibido.','override = declaracion explicita de sobreescritura.','Intermedio'),
        mk(9,3,'Metodo const avanzado','¿Por que es buena practica declarar const los metodos que no modifican el objeto?',None,
           'Para poder usarlos con objetos const y documentar que no cambian el estado',['Para hacerlos mas rapidos','Es obligatorio en C++ moderno','Para que puedan heredarse'],
           'Un metodo const puede llamarse desde objetos declarados como const. Sin const el compilador rechaza la llamada. Ademas documenta claramente la intencion del metodo.','const = promesa verificada por el compilador.','Avanzado'),
    ]
    for e in EJS:
        c.execute("""INSERT OR IGNORE INTO ejercicios
            (modulo_id,numero,titulo,descripcion,codigo_base,
             opcion_a,opcion_b,opcion_c,opcion_d,
             respuesta_correcta,explicacion,pista,dificultad)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", e)
    conn.commit()

def _seed_admin(c, conn):
    from werkzeug.security import generate_password_hash
    if not c.execute("SELECT id FROM usuarios WHERE email='admin@sistema.com'").fetchone():
        c.execute("""INSERT INTO usuarios(nombre,apellido,email,password_hash,rol_id)
            VALUES('Admin','Sistema','admin@sistema.com',?,1)""",
            (generate_password_hash('admin123'),))
        conn.commit()
        print("[DB] Admin: admin@sistema.com / admin123")
