# cppLearn — Plataforma de Aprendizaje de C++
### Universidad Central 2025

---

## TECNOLOGIAS UTILIZADAS

| Capa | Tecnologia | Descripcion |
|---|---|---|
| Backend | Python 3 + Flask | Servidor web, rutas, logica de negocio |
| Base de datos | SQLite (sqlite3) | Archivo local cpplearn.db |
| Seguridad | Werkzeug (pbkdf2:sha256) | Encriptacion de contrasenas |
| Sesiones | Flask session nativa | Cookie firmada con SECRET_KEY |
| Frontend | HTML5 + CSS3 + JS | Sin frameworks externos |

---

## ESTRUCTURA DEL PROYECTO

```
cpplearn/
├── app.py                      <- Punto de entrada principal
├── requirements.txt            <- Solo necesita Flask
├── cpplearn.db                 <- BD SQLite (se crea automaticamente al iniciar)
├── config/
│   ├── __init__.py
│   └── settings.py             <- SECRET_KEY, ruta de la base de datos
├── models/
│   ├── __init__.py
│   ├── database.py             <- Conexion, tablas, datos iniciales
│   └── user.py                 <- Clase User
├── controllers/
│   ├── __init__.py
│   ├── auth_controller.py      <- Registro y login
│   └── course_controller.py   <- Modulos, ejercicios, progreso
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py          <- /login  /registro  /logout
│   └── course_routes.py       <- /dashboard /modulo /perfil /admin
└── templates/
    ├── shared/base.html        <- Layout con sidebar
    ├── shared/error.html       <- Errores 403/404
    ├── auth/login.html
    ├── auth/registro.html
    ├── student/dashboard.html
    ├── student/modulo.html
    ├── student/leccion.html
    ├── student/perfil.html
    └── admin/panel.html
```

---

## INSTALACION EN WINDOWS

```cmd
rem 1. Abre CMD en la carpeta cpplearn
cd C:\Users\karol\Downloads\cpplearn

rem 2. Instala Flask (unica dependencia)
pip install flask

rem 3. Corre la aplicacion
python app.py

rem 4. Abre: http://localhost:5000
```

La base de datos cpplearn.db se crea automaticamente.
El usuario admin se crea automaticamente: admin@cpplearn.com / admin123

---

## ROLES Y PERMISOS

| Rol | Acceso |
|---|---|
| Administrador | Dashboard, todos los modulos, panel /admin, gestionar usuarios |
| Estudiante | Su dashboard, modulos desbloqueados, su perfil |

El control de acceso se implementa con decoradores en routes/:
- @login_required  -> redirige a /login si no hay sesion
- @solo_admin      -> retorna 403 si el usuario no es administrador

---

## CUANDO SE REGISTRA UN USUARIO

1. Se valida que el correo no exista (UNIQUE en SQLite)
2. La contrasena se encripta con pbkdf2:sha256
3. Se guarda en la tabla usuarios con rol_id=2 (Estudiante)
4. Se crea la sesion Flask con el user_id
5. Los modulos 1 y 2 quedan disponibles inmediatamente

Si el correo ya existe: "Este correo electronico ya esta registrado."

---

*Proyecto academico - Universidad Central 2025*
