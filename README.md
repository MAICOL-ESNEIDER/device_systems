# device_systems — API REST para Gestión de Usuarios (v2.1.0)

Proyecto de las actividades **EV07** (Fundamentos de FastAPI), **EV08** (CRUD completo y Dependency Injection) y **EV09 — FastAPI con SQLAlchemy: Persistencia de Datos**. A partir de esta versión, los usuarios se almacenan, consultan, actualizan y eliminan desde una **base de datos real** (SQLite vía SQLAlchemy), dejando atrás la lista en memoria de las versiones anteriores.

## 📋 Descripción de la API

`device_systems` gestiona el recurso `users` con las siguientes capacidades:
- **Crear**, **listar** (con filtros por rol/estado), **consultar por ID**, **actualizar completa o parcialmente**, y **eliminar** usuarios.
- Validación de datos con **Pydantic v2**.
- Manejo de errores estructurado con `HTTPException` (404, 400, 401, 422).
- **4 dependencias reutilizables** con `Depends()`: búsqueda por ID, validación de PATCH vacío, autenticación simulada por cabecera, y configuración general de la API.
- Documentación automática enriquecida en Swagger UI y ReDoc.
- Todas las respuestas incluyen **cabeceras HTTP personalizadas** (`X-App-Name`, `X-API-Version`).

Los datos se guardan en memoria (no hay base de datos externa) — suficiente para el alcance de este reto académico; el servidor arranca con 4 usuarios de ejemplo ya cargados.

## 🛠️ Tecnologías utilizadas

- **FastAPI** 0.141.1 — framework web
- **Uvicorn** 0.52.4 — servidor ASGI
- **SQLAlchemy** 2.0.53 — ORM y persistencia en base de datos (EV09)
- **SQLite** — motor de base de datos para desarrollo
- **Pydantic** 2.13.5 — validación de datos
- **email-validator** — validación de formato de correo

## 📁 Estructura del proyecto

```
device_systems/
├── app/
│   ├── main.py                     # Instancia de FastAPI, middleware, endpoint raíz
│   ├── database/
│   │   └── connection.py           # Engine, SessionLocal y Base de SQLAlchemy (EV09)
│   ├── models/
│   │   └── user_model.py           # Modelo ORM de la tabla 'users' (EV09)
│   ├── routes/
│   │   └── user_routes.py          # Endpoints HTTP (solo reciben/traducen, no tienen lógica de negocio)
│   ├── schemas/
│   │   └── user_schema.py          # Modelos Pydantic: UserCreate, UserUpdate, UserPatch, UserResponse
│   ├── services/
│   │   └── user_service.py         # Lógica de negocio sobre la base de datos (sin HTTP)
│   └── dependencies/
│       ├── database_dependency.py  # get_db(): entrega y cierra la sesión de BD (EV09)
│       └── user_dependencies.py    # Funciones reutilizables inyectadas con Depends()
├── images/                         # Capturas de Swagger UI / ReDoc / estructura / BD
├── device_systems.db               # Base de datos SQLite (se genera sola, no se sube a git)
├── requirements.txt
├── .gitignore
└── README.md
```

### ¿Qué diferencia hay entre un modelo SQLAlchemy y un schema Pydantic?

Esta es una de las confusiones más comunes al empezar con FastAPI + SQLAlchemy, porque ambos "describen" a un usuario, pero cumplen roles completamente distintos:

| | `app/models/user_model.py` (SQLAlchemy) | `app/schemas/user_schema.py` (Pydantic) |
|---|---|---|
| **Qué representa** | Una **tabla** de la base de datos | El **contrato** de entrada/salida de la API (el JSON que viaja por HTTP) |
| **De qué hereda** | `Base` (declarative base de SQLAlchemy) | `BaseModel` (Pydantic) |
| **Vive mientras...** | ...existe una fila en la base de datos | ...dura una petición HTTP |
| **Ejemplo de diferencia** | `email = Column(String, unique=True, ...)` — restricción a nivel de base de datos | `email: EmailStr` — validación a nivel de request/response |
| **Puede haber varios por recurso** | No, un solo modelo `User` para toda la tabla | Sí: `UserCreate`, `UserUpdate`, `UserPatch`, `UserResponse` — cada uno expone/exige campos distintos según el momento |

En la práctica: cuando llega un `POST /users`, Pydantic (`UserCreate`) valida el JSON de entrada; la ruta usa esos datos ya validados para crear un objeto `User` de SQLAlchemy, que se guarda en la tabla; y al responder, ese objeto `User` se convierte de vuelta a `UserResponse` (gracias a `model_config = ConfigDict(from_attributes=True)`) para enviarlo como JSON. Ninguno de los dos reemplaza al otro — se complementan en distintos puntos del flujo de una petición.

### ¿Por qué esta separación en capas?
- **`routes`**: solo entiende de HTTP (status codes, path/query/body). No sabe *cómo* se guarda un usuario.
- **`services`**: solo entiende de la lógica de negocio (buscar, crear, actualizar, eliminar). Recibe la sesión de base de datos como parámetro, pero no sabe nada de FastAPI ni de HTTPException.
- **`dependencies`**: valida cosas que varias rutas necesitan (existencia del usuario, autorización, la propia sesión de BD), evitando repetir el mismo código en cada endpoint.
- **`database`**: configura *cómo* se conecta la aplicación a la base de datos (una sola vez, al importar el módulo).
- **`models`**: define la *estructura de las tablas* (columnas, tipos, restricciones) — completamente separado de los `schemas`, que definen el contrato de la API (ver la explicación arriba).

## ⚙️ Instalación de dependencias

```bash
git clone https://github.com/MAICOL-ESNEIDER/device_systems.git
cd device_systems

python -m venv venv
venv\Scripts\Activate.ps1        # Windows (PowerShell)
# source venv/bin/activate       # Linux/Mac

pip install -r requirements.txt
```

## ▶️ Ejecución del servidor

```bash
uvicorn app.main:app --reload
```

- API: `http://127.0.0.1:8000`
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 🌐 Tabla de endpoints y códigos de estado

| Operación | Método | Ruta | Código de éxito | Código de error |
|---|---|---|---|---|
| Listar usuarios | `GET` | `/users` | 200 OK | — |
| Filtrar por rol/estado | `GET` | `/users?role=admin` / `?is_active=true` | 200 OK | — |
| Consultar por ID | `GET` | `/users/{user_id}` | 200 OK | 404 Not Found |
| Crear usuario | `POST` | `/users` | 201 Created | 400 (correo duplicado) / 422 (datos inválidos) |
| Actualizar completo | `PUT` | `/users/{user_id}` | 200 OK | 404 / 400 (correo duplicado) |
| Actualizar parcial | `PATCH` | `/users/{user_id}` | 200 OK | 404 / 400 (sin campos o correo duplicado) |
| Eliminar usuario | `DELETE` | `/users/{user_id}` | 204 No Content | 404 / 401 (sin autorización) |

Todas las respuestas incluyen las cabeceras `X-App-Name: device_systems` y `X-API-Version: 2.1`.

> A partir de EV09, estas operaciones ya no se guardan en una lista en memoria: se persisten en la tabla `users` de `device_systems.db` (SQLite). El archivo de base de datos se crea solo la primera vez que se ejecuta el servidor.

---

## 🧪 Ejemplos de peticiones y respuestas (probados con TestClient antes de subir)

### GET /users
```json
[
  {"name": "Camila Restrepo", "email": "camila@ejemplo.com", "role": "admin", "is_active": true, "id": 1},
  {"name": "Andrés Gómez", "email": "andres@ejemplo.com", "role": "support", "is_active": true, "id": 2},
  {"name": "Laura Pérez", "email": "laura@ejemplo.com", "role": "user", "is_active": false, "id": 3},
  {"name": "Pedro Sánchez", "email": "pedro@ejemplo.com", "role": "user", "is_active": true, "id": 4}
]
```

### GET /users?role=admin
```json
[{"name": "Camila Restrepo", "email": "camila@ejemplo.com", "role": "admin", "is_active": true, "id": 1}]
```

### GET /users/2
```json
{"name": "Andrés Gómez", "email": "andres@ejemplo.com", "role": "support", "is_active": true, "id": 2}
```

### GET /users/999 (no existe) → `404 Not Found`
```json
{"detail": "Usuario no encontrado"}
```

### POST /users (caso válido) → `201 Created`
Body:
```json
{"name": "Sofía Vargas", "email": "sofia@ejemplo.com", "role": "user", "is_active": true}
```
Respuesta:
```json
{"name": "Sofía Vargas", "email": "sofia@ejemplo.com", "role": "user", "is_active": true, "id": 5}
```

### POST /users (correo duplicado) → `400 Bad Request`
```json
{"detail": "Ya existe un usuario registrado con el correo 'sofia@ejemplo.com'"}
```

### POST /users (rol inválido) → `422 Unprocessable Entity`
```json
{"detail": [{"type": "enum", "loc": ["body", "role"], "msg": "Input should be 'admin', 'support' or 'user'", "input": "superadmin"}]}
```

### PUT /users/3 (actualización completa) → `200 OK`
Body:
```json
{"name": "Laura Pérez G.", "email": "laura.g@ejemplo.com", "role": "admin", "is_active": true}
```
Respuesta:
```json
{"name": "Laura Pérez G.", "email": "laura.g@ejemplo.com", "role": "admin", "is_active": true, "id": 3}
```

### PATCH /users/2 (actualización parcial — solo el rol) → `200 OK`
Body:
```json
{"role": "admin"}
```
Respuesta:
```json
{"name": "Andrés Gómez", "email": "andres@ejemplo.com", "role": "admin", "is_active": true, "id": 2}
```

### PATCH /users/2 (body vacío) → `400 Bad Request`
```json
{"detail": "Debes enviar al menos un campo para actualizar"}
```

### DELETE /users/4 sin cabecera de autorización → `401 Unauthorized`
```json
{"detail": "Cabecera X-API-Key ausente o inválida"}
```

### DELETE /users/4 con `X-API-Key: device-systems-secret-key` → `204 No Content`
*(sin cuerpo de respuesta)*

### GET /users?role=user&order_by=name (EV09 — filtro + orden sobre la base de datos)
```json
[
  {"name": "Andrés Gómez", "email": "andres@ejemplo.com", "role": "user", "is_active": true, "id": 2, "created_at": "2026-09-16T18:44:44.815552"},
  {"name": "Pedro Sánchez", "email": "pedro@ejemplo.com", "role": "user", "is_active": true, "id": 4, "created_at": "2026-09-16T18:45:01.120441"}
]
```

### Prueba de persistencia real (EV09)
Antes de subir el proyecto se verificó que los datos realmente quedan guardados en la base de datos —no solo que la API "responde bien"— consultando la tabla `users` directamente con `sqlite3`, sin pasar por la API:
```
$ sqlite3 device_systems.db "SELECT id, name, email, role, is_active, created_at FROM users;"
1|Camila Restrepo|camila@ejemplo.com|admin|0|2026-09-16 18:44:44.732304
2|Andrés Gómez|andres@ejemplo.com|admin|1|2026-09-16 18:44:44.815552
3|Laura P.|laura.p@ejemplo.com|admin|1|2026-09-16 18:44:44.920103
```
Esto confirma que `db.commit()` efectivamente persiste los cambios en disco, y que reiniciar el servidor no borra los datos (a diferencia de la lista en memoria de EV07/EV08).

---

## 🔌 Explicación del uso de `Depends()` (Dependency Injection)

El proyecto define 4 dependencias en `app/dependencies/user_dependencies.py`:

| Dependencia | Qué valida | Dónde se usa |
|---|---|---|
| `get_user_or_404(user_id)` | Busca el usuario por su path parameter; lanza 404 si no existe | `GET`, `PUT`, `PATCH`, `DELETE` por ID |
| `validar_patch_no_vacio(datos)` | Verifica que el body del PATCH tenga al menos un campo distinto de `None` | `PATCH /users/{user_id}` |
| `verificar_api_key(x_api_key)` | Simula autenticación leyendo la cabecera `X-API-Key` | `DELETE /users/{user_id}` |
| `obtener_configuracion_api()` | Expone el nombre y versión de la app (dependencia sin parámetros) | `GET /` |

La ventaja principal: **`get_user_or_404` se declara una sola vez** y se reutiliza en 4 endpoints distintos. Sin `Depends()`, cada uno tendría que repetir la misma búsqueda + el mismo `if usuario is None: raise HTTPException(...)`.

> **Nota técnica:** la guía también sugiere dependencias para "validar correo duplicado" y "validar rol permitido". El rol ya queda cubierto automáticamente por Pydantic (el `Enum` del schema rechaza cualquier valor fuera de `admin/support/user` con un 422, sin código adicional). El correo duplicado sí se valida como lógica de negocio (`user_service.obtener_usuario_por_email()`), pero se invoca directamente desde las rutas en vez de como una dependencia `Depends()` separada: convertirla en dependencia recibiendo el mismo modelo Pydantic del body que ya recibe el propio endpoint hace que FastAPI interprete que hay *dos* cuerpos distintos y exija el JSON anidado en dos claves, rompiendo la petición plana que envía un cliente normal. Se priorizó una implementación simple y funcionalmente correcta sobre forzar ese patrón.

---

## ⚠️ Explicación del manejo de errores implementado

Se usa `HTTPException` en 4 escenarios distintos:

1. **Usuario no encontrado** (404) — en `get_user_or_404`, reutilizada por 4 endpoints.
2. **Correo electrónico duplicado** (400) — validado en `POST`, `PUT` y `PATCH`, excluyendo al propio usuario al actualizar (para no marcarlo como duplicado de sí mismo).
3. **PATCH sin ningún campo enviado** (400) — validado por la dependencia `validar_patch_no_vacio`.
4. **Autorización faltante en DELETE** (401) — validado por `verificar_api_key`.

Pydantic maneja automáticamente un quinto caso: **datos inválidos** (422) — nombre muy corto, correo mal formado, o rol fuera de `admin/support/user`.

---

## 🖥️ Capturas de Swagger UI y ReDoc

**Swagger UI — vista general de los endpoints:**
![Swagger UI general](images/swagger_1_vista_general.png)

**Prueba GET /users:**
![Prueba GET /users](images/swagger_2_get_users.png)

**Prueba GET /users/{user_id}:**
![Prueba GET /users/id](images/swagger_3_get_user_id.png)

**Prueba POST /users:**
![Prueba POST /users](images/swagger_4_post_users.png)

**Evidencia de validación — correo duplicado:**
![Evidencia correo duplicado](images/swagger_5_validacion_error.png)

**Evidencia de validación — rol inválido:**
![Evidencia rol inválido](images/swagger_6_validacion_error.png)

**Prueba PUT /users/{user_id} (EV08):**
![Prueba PUT](images/swagger_7_put_users.png)

**Prueba PATCH /users/{user_id} (EV08):**
![Prueba PATCH](images/swagger_8_patch_users.png)

**Prueba DELETE /users/{user_id} con cabecera X-API-Key (EV08):**
![Prueba DELETE](images/swagger_9_delete_users.png)

**Evidencia de error controlado — DELETE sin autorización, 401 (EV08):**
![Evidencia error 401](images/swagger_10_error_controlado.png)

**Evidencia — usuario no encontrado, 404:**
![Evidencia 404](images/swagger_11_404_no_encontrado.png)

**Evidencia — PATCH sin campos, 400:**
![Evidencia PATCH vacío](images/swagger_12_patch_vacio.png)

**ReDoc — documentación alternativa (EV08):**
![ReDoc](images/redoc_vista_general_1.png)
![ReDoc](images/redoc_vista_general_2.png)
![ReDoc](images/redoc_vista_general_3.png)
![ReDoc](images/redoc_vista_general_4.png)
![ReDoc](images/redoc_vista_general_5.png)

**Estructura del proyecto en el editor (EV09):**
![Estructura del proyecto](images/ev09_1_estructura_proyecto.png)

**Base de datos generada — tabla `users` en `device_systems.db` (EV09):**
![Base de datos generada](images/ev09_2_base_datos_generada.png)

**Swagger UI — GET /users con filtro y orden aplicados (EV09):**
![GET con filtro y orden](images/ev09_3_get_filtro_orden.png)

**Evidencia de persistencia — datos tras reiniciar el servidor (EV09):**
![Evidencia de persistencia](images/ev09_4_persistencia.png)

---

## 🌿 Estrategia de ramas (Git Flow)

```
main
 └── develop
      ├── feature/estructura-proyecto            (EV07 — estructura base FastAPI)
      ├── feature/modelos-pydantic               (EV07 — UserBase, UserCreate, UserResponse)
      ├── feature/endpoints-get                  (EV07 — GET /users, GET /users/{id})
      ├── feature/endpoints-post                 (EV07 — POST /users)
      ├── feature/response-models-headers        (EV07 — middleware de cabeceras)
      ├── feature/documentacion                  (EV07 — README v1)
      ├── feature/arquitectura-servicios-data     (EV08 — capas data/services)
      ├── feature/dependency-injection            (EV08 — dependencias con Depends())
      ├── feature/put-patch-delete                (EV08 — CRUD completo)
      ├── feature/swagger-docs-v2                 (EV08 — metadatos v2.0.0 + README v2)
      ├── feature/sqlalchemy-setup                (EV09 — conexión SQLAlchemy + modelo User)
      ├── feature/schemas-db                      (EV09 — schemas actualizados + get_db)
      ├── feature/crud-usuarios-db                (EV09 — CRUD real sobre la base de datos)
      └── feature/documentacion-ev09              (EV09 — este README)
```

Cada feature se desarrolló, se probó, y se integró a `develop` con un merge commit (`--no-ff`). `develop` se fusionó en `main` en cada entrega: **v1.0.0** (EV07), **v2.0.0** (EV08), **v2.1.0** (EV09). Ninguna rama se elimina tras el merge, para conservar visible el historial de cómo se construyó cada versión.

---

## 🧠 Reflexión sobre la evolución del proyecto

Pasar de la versión EV07 (solo GET y POST, guardando los datos directamente en el router) a esta versión con capas separadas me hizo notar cuánto crece la complejidad real de una API a medida que se le agregan operaciones. Con solo GET y POST, tener todo en un archivo no se sentía problemático; pero al agregar PUT, PATCH y DELETE — cada uno con sus propias reglas de validación — repetir la búsqueda del usuario y el manejo del 404 en cada endpoint se hubiera vuelto muy repetitivo. Ahí entendí el valor real de `Depends()`: no es solo "otra forma de recibir parámetros", es una manera de declarar una regla de validación *una sola vez* y confiar en que FastAPI la aplique donde se necesite.

La diferencia entre PUT y PATCH también se aclaró mucho al implementarlos: PUT obliga a pensar en el recurso como algo que se reemplaza entero (por eso todos los campos son obligatorios en `UserUpdate`), mientras que PATCH obliga a pensar en qué pasa cuando un campo *no* se envía — ahí es donde `Optional` y `exclude_none` en Pydantic se volvieron indispensables.

Por último, separar `services` de `routes` me hizo ver una ventaja que no esperaba: al no depender de FastAPI, la lógica de negocio se puede probar y entender sin siquiera saber qué es un endpoint HTTP. Eso hace más fácil razonar sobre errores: si algo falla, sé de inmediato si el problema está en cómo se valida el HTTP o en la lógica en sí.

También aprendí (de la manera difícil, resolviendo un conflicto de Git real) que documentar bien la evolución de un proyecto importa tanto como el código: perder de vista qué evidencia ya existía de una versión anterior es un error fácil de cometer al fusionar ramas, y vale la pena revisar con calma en vez de asumir que un merge se resolvió como uno esperaba.

### Sobre la importancia de la persistencia (EV09)

Trabajar con una lista en memoria en EV07/EV08 era cómodo para enfocarse en aprender FastAPI, pero escondía un problema serio: **cada vez que el servidor se reiniciaba, todos los datos desaparecían**. Eso es completamente inaceptable para cualquier aplicación real — nadie usaría un sistema donde reiniciar el servidor borra a todos los usuarios registrados. Migrar a SQLAlchemy me hizo valorar algo que antes daba por sentado: la diferencia entre un programa que *simula* guardar datos y uno que realmente los persiste en disco.

También entendí mejor la responsabilidad de una sesión de base de datos: no es solo "un objeto para hacer consultas", es un recurso que hay que abrir y cerrar correctamente por cada petición — de ahí el patrón `yield` + `finally` en `get_db()`, que garantiza que la sesión se cierre incluso si algo falla a mitad de una petición. Sin ese patrón, cada error dejaría conexiones abiertas que eventualmente agotarían los recursos del servidor.

Por último, separar el modelo SQLAlchemy del schema Pydantic —aunque a primera vista se sienta como "escribir el mismo usuario dos veces"— resolvió un problema que no había anticipado: la tabla de la base de datos y el contrato de la API no siempre deberían evolucionar juntos. Puedo agregar una columna interna a `User` (por ejemplo, para auditoría) sin que eso se filtre automáticamente a la respuesta de la API, precisamente porque `UserResponse` decide explícitamente qué se expone.

## 👤 Autor

Proyecto desarrollado por **Maicol Esneider** como evidencia de aprendizaje de las actividades *Fundamentos de FastAPI* (EV07), *FastAPI Intermedio: Evolución con CRUD Completo* (EV08) y *FastAPI con SQLAlchemy: Persistencia de Datos* (EV09).