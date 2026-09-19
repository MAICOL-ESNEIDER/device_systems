# device_systems — API REST de Usuarios, Dispositivos y Préstamos (v3.0.0)

Proyecto de las actividades **EV07** (Fundamentos de FastAPI), **EV08** (CRUD completo y Dependency Injection), **EV09** (persistencia con SQLAlchemy) y **EV10 — FastAPI Avanzado: Migraciones con Alembic, Asociaciones de Modelos y Consultas con Joins**. En esta versión el sistema deja de administrar solo usuarios: ahora gestiona también **dispositivos** (`/devices`) y **préstamos** (`/loans`), con relaciones reales entre las 3 tablas, el esquema de base de datos versionado con **Alembic**, y consultas que combinan información de varias tablas con **joins**.

## 📋 Descripción de la API

`device_systems` gestiona 3 recursos relacionados entre sí:

- **`/users`** — Crear, listar (con filtros por rol/estado, orden por nombre/fecha), consultar por ID, actualizar completa o parcialmente, eliminar, y consultar el historial de préstamos de un usuario.
- **`/devices`** — CRUD completo con filtros por tipo, disponibilidad, marca y búsqueda de texto libre; consultar el historial de préstamos de un dispositivo.
- **`/loans`** — Registrar un préstamo (validando que el usuario exista, el dispositivo exista y esté disponible), devolverlo, listar con filtros (incluyendo filtros que requieren JOIN hacia otras tablas), y una vista detallada que combina las 3 tablas en una sola respuesta.

Además:
- Validación de datos con **Pydantic v2**, incluyendo esquemas anidados (`LoanDetailResponse`).
- Manejo de errores con `HTTPException` (404, 400, 401, 409, 422).
- Esquema de base de datos versionado con **Alembic** (migraciones controladas, no `create_all()`).
- Relaciones reales entre modelos (`ForeignKey`, `relationship()`, `back_populates`).
- Documentación automática en Swagger UI y ReDoc, organizada por tags (`Users`, `Devices`, `Loans`, `Root`).
- Todas las respuestas incluyen cabeceras HTTP personalizadas (`X-App-Name`, `X-API-Version`).

## 🛠️ Tecnologías utilizadas

- **FastAPI** 0.141.1 — framework web
- **Uvicorn** 0.52.4 — servidor ASGI
- **SQLAlchemy** 2.0.53 — ORM y persistencia en base de datos (EV09)
- **Alembic** 1.20.0 — migraciones de base de datos versionadas (EV10)
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
│   │   ├── user_model.py           # Tabla 'users' (EV09) + relación loans (EV10)
│   │   ├── device_model.py         # Tabla 'devices' (EV10)
│   │   └── loan_model.py           # Tabla 'loans': ForeignKey a users y devices (EV10)
│   ├── routes/
│   │   ├── user_routes.py          # Endpoints de /users + GET /users/{id}/loans
│   │   ├── device_routes.py        # Endpoints de /devices + GET /devices/{id}/loans
│   │   └── loan_routes.py          # Endpoints de /loans, incluyendo /loans/details (joins)
│   ├── schemas/
│   │   ├── user_schema.py          # UserCreate, UserUpdate, UserPatch, UserResponse
│   │   ├── device_schema.py        # DeviceCreate, DeviceUpdate, DevicePatch, DeviceResponse
│   │   └── loan_schema.py          # LoanCreate, LoanResponse, LoanDetailResponse (anidado)
│   ├── services/
│   │   ├── user_service.py         # Lógica de negocio de usuarios
│   │   ├── device_service.py       # Lógica de negocio de dispositivos + filtros
│   │   └── loan_service.py         # Reglas de préstamo/devolución + consultas con JOIN
│   └── dependencies/
│       ├── database_dependency.py  # get_db(): entrega y cierra la sesión de BD
│       └── user_dependencies.py    # Dependencias reutilizables con Depends()
├── alembic/
│   ├── env.py                      # Configuración de Alembic: importa Base y los 3 modelos
│   └── versions/                   # Migraciones generadas (historial versionado del esquema)
├── alembic.ini                     # URL de conexión que usa Alembic
├── images/                         # Capturas de Swagger UI / ReDoc / estructura / BD / Alembic
├── device_systems.db               # Base de datos SQLite (se genera con Alembic, no se sube a git)
├── requirements.txt
├── .gitignore
└── README.md
```

### ¿Qué diferencia hay entre un modelo SQLAlchemy y un schema Pydantic?

Esta es una de las confusiones más comunes al empezar con FastAPI + SQLAlchemy, porque ambos "describen" un recurso, pero cumplen roles completamente distintos:

| | `app/models/*.py` (SQLAlchemy) | `app/schemas/*.py` (Pydantic) |
|---|---|---|
| **Qué representa** | Una **tabla** de la base de datos | El **contrato** de entrada/salida de la API (el JSON que viaja por HTTP) |
| **De qué hereda** | `Base` (declarative base de SQLAlchemy) | `BaseModel` (Pydantic) |
| **Vive mientras...** | ...existe una fila en la base de datos | ...dura una petición HTTP |
| **Ejemplo de diferencia** | `email = Column(String, unique=True, ...)` — restricción a nivel de base de datos | `email: EmailStr` — validación a nivel de request/response |
| **Relaciones** | `relationship()` conecta objetos Python automáticamente (`prestamo.user.name`) | Un schema anidado (`LoanDetailResponse.user: LoanUserSummary`) arma manualmente esa misma información para la respuesta JSON |
| **Puede haber varios por recurso** | No, un solo modelo `User`/`Device`/`Loan` por tabla | Sí: por ejemplo `UserCreate`, `UserUpdate`, `UserPatch`, `UserResponse` — cada uno expone/exige campos distintos según el momento |

En la práctica: cuando llega un `POST /users`, Pydantic (`UserCreate`) valida el JSON de entrada; la ruta usa esos datos ya validados para crear un objeto `User` de SQLAlchemy, que se guarda en la tabla; y al responder, ese objeto `User` se convierte de vuelta a `UserResponse` (gracias a `model_config = ConfigDict(from_attributes=True)`) para enviarlo como JSON. Ninguno de los dos reemplaza al otro — se complementan en distintos puntos del flujo de una petición.

### ¿Por qué esta separación en capas?
- **`routes`**: solo entiende de HTTP (status codes, path/query/body). No sabe *cómo* se guarda un usuario.
- **`services`**: solo entiende de la lógica de negocio (buscar, crear, actualizar, eliminar, validar reglas). Recibe la sesión de base de datos como parámetro, pero no sabe nada de FastAPI ni de HTTPException.
- **`dependencies`**: valida cosas que varias rutas necesitan (existencia del usuario, autorización, la propia sesión de BD), evitando repetir el mismo código en cada endpoint.
- **`database`**: configura *cómo* se conecta la aplicación a la base de datos (una sola vez, al importar el módulo).
- **`models`**: define la *estructura de las tablas* (columnas, tipos, restricciones, relaciones) — completamente separado de los `schemas`.
- **`alembic`**: versiona los *cambios* al esquema a lo largo del tiempo (ver la sección de migraciones más abajo).

---

## 🔗 Asociaciones entre modelos (EV10)

El sistema relaciona 3 tablas con **integridad referencial real**, no solo "IDs sueltos":

```
User (1) ──────< Loan >────── (1) Device
     "un usuario           "un dispositivo puede
      puede tener           aparecer en muchos
      muchos préstamos"     préstamos históricos"
```

- **`Loan.user_id`** y **`Loan.device_id`** son `ForeignKey("users.id")` / `ForeignKey("devices.id")`: la base de datos **rechaza** cualquier intento de crear un préstamo que apunte a un usuario o dispositivo inexistente (además, la API ya valida esto antes y devuelve 404 con un mensaje claro, en vez de dejar que falle la base de datos).
- **`relationship()` + `back_populates`** conectan ambos lados de cada relación: `usuario.loans` da la lista de préstamos de ese usuario sin escribir una consulta manual, y `prestamo.user.name` accede al nombre del usuario dueño del préstamo navegando el objeto directamente (SQLAlchemy resuelve el JOIN por debajo cuando se accede a ese atributo).
- Es una relación **uno a muchos** en ambos sentidos: un usuario → muchos préstamos, un dispositivo → muchos préstamos (históricos), pero cada préstamo individual pertenece a exactamente un usuario y un dispositivo.

## 🧬 Migraciones con Alembic (EV10)

Antes de EV10, las tablas se creaban con `Base.metadata.create_all()` al iniciar el servidor — funcional, pero sin ningún historial de *cómo* cambió el esquema con el tiempo, y sin forma de deshacer un cambio. Alembic resuelve esto:

1. **`alembic init alembic`** — genera la estructura de carpetas y `alembic.ini`.
2. **Configuración en `alembic/env.py`** — se importa `Base` y **cada modelo explícitamente** (`User`, `Device`, `Loan`); si un modelo no se importa aquí, Alembic no lo "ve" y no lo incluye al comparar el esquema.
3. **`alembic revision --autogenerate -m "..."`** — Alembic compara `Base.metadata` (lo que dicen los modelos) contra el estado real de la base de datos, y genera automáticamente el archivo de migración con las diferencias (`CREATE TABLE`, columnas nuevas, índices, etc.).
4. **`alembic upgrade head`** — aplica la migración pendiente más reciente.
5. **`alembic history`** — muestra el historial de migraciones aplicadas, en orden.

La migración inicial de este proyecto (`alembic/versions/6c9a9b8efc7b_create_users_devices_and_loans_tables.py`) crea las 3 tablas de una vez, porque el esquema completo (incluyendo `users`, que ya existía desde EV09) se adoptó bajo Alembic en este mismo momento — a partir de aquí, cualquier cambio futuro al esquema se hace con una migración nueva, nunca modificando la base de datos a mano.

## ⚙️ Instalación de dependencias

```bash
git clone https://github.com/MAICOL-ESNEIDER/device_systems.git
cd device_systems

python -m venv venv
venv\Scripts\Activate.ps1        # Windows (PowerShell)
# source venv/bin/activate       # Linux/Mac

pip install -r requirements.txt
```

## 🗄️ Aplicar las migraciones (obligatorio antes de correr el servidor)

```bash
alembic upgrade head
```

Esto crea `device_systems.db` con las 3 tablas ya listas. Si quieres ver el detalle de cómo se generó esa migración (para tomar tus propias capturas de evidencia), puedes borrar `device_systems.db` y `alembic/versions/*.py`, y regenerar todo desde cero:
```bash
rm device_systems.db alembic/versions/*.py     # Linux/Mac
# del device_systems.db, alembic\versions\*.py   # Windows

alembic revision --autogenerate -m "create users devices and loans tables"
alembic upgrade head
alembic history
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

### Users
| Operación | Método | Ruta | Código de éxito | Código de error |
|---|---|---|---|---|
| Listar usuarios | `GET` | `/users` | 200 OK | — |
| Filtrar / ordenar | `GET` | `/users?role=admin` · `?is_active=true` · `?order_by=name` | 200 OK | — |
| Consultar por ID | `GET` | `/users/{user_id}` | 200 OK | 404 Not Found |
| Historial de préstamos | `GET` | `/users/{user_id}/loans` | 200 OK | 404 Not Found |
| Crear usuario | `POST` | `/users` | 201 Created | 400 (correo duplicado) / 422 (datos inválidos) |
| Actualizar completo | `PUT` | `/users/{user_id}` | 200 OK | 404 / 400 (correo duplicado) |
| Actualizar parcial | `PATCH` | `/users/{user_id}` | 200 OK | 404 / 400 (sin campos o correo duplicado) |
| Eliminar usuario | `DELETE` | `/users/{user_id}` | 204 No Content | 404 / 401 (sin autorización) |

### Devices (EV10)
| Operación | Método | Ruta | Código de éxito | Código de error |
|---|---|---|---|---|
| Listar dispositivos | `GET` | `/devices` | 200 OK | — |
| Filtrar / buscar | `GET` | `/devices?device_type=laptop` · `?is_available=true` · `?brand=lenovo` · `?search=thinkpad` | 200 OK | — |
| Consultar por ID | `GET` | `/devices/{device_id}` | 200 OK | 404 Not Found |
| Historial de préstamos | `GET` | `/devices/{device_id}/loans` | 200 OK | 404 Not Found |
| Crear dispositivo | `POST` | `/devices` | 201 Created | 400 (serial duplicado) / 422 |
| Actualizar completo | `PUT` | `/devices/{device_id}` | 200 OK | 404 / 400 (serial duplicado) |
| Actualizar parcial | `PATCH` | `/devices/{device_id}` | 200 OK | 404 |
| Eliminar dispositivo | `DELETE` | `/devices/{device_id}` | 204 No Content | 404 |

### Loans (EV10)
| Operación | Método | Ruta | Código de éxito | Código de error |
|---|---|---|---|---|
| Listar préstamos | `GET` | `/loans` | 200 OK | — |
| Filtrar (con JOIN) | `GET` | `/loans?status=active` · `?user_email=...` · `?device_type=laptop` | 200 OK | — |
| Detalle con joins | `GET` | `/loans/details` | 200 OK | — |
| Consultar por ID | `GET` | `/loans/{loan_id}` | 200 OK | 404 Not Found |
| Crear préstamo | `POST` | `/loans` | 201 Created | 404 (usuario o dispositivo no existe) / 409 (dispositivo no disponible) |
| Devolver préstamo | `PATCH` | `/loans/{loan_id}/return` | 200 OK | 404 (no existe) / 409 (ya devuelto) |

Todas las respuestas incluyen las cabeceras `X-App-Name: device_systems` y `X-API-Version: 3.0`.

> A partir de EV09, estas operaciones ya no se guardan en una lista en memoria: se persisten en `device_systems.db` (SQLite), y desde EV10 el esquema se gestiona con Alembic (ver la sección de migraciones más arriba).

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

### POST /devices (EV10) → `201 Created`
```json
{"name": "Laptop Lenovo ThinkPad", "serial_number": "LEN-2024-001", "device_type": "laptop", "brand": "Lenovo", "is_available": true, "id": 1, "created_at": "2026-09-17T02:40:23.400000"}
```

### POST /loans (EV10 — dispositivo disponible) → `201 Created`
Body: `{"user_id": 1, "device_id": 1}`
```json
{"id": 1, "user_id": 1, "device_id": 1, "loan_date": "2026-09-17T02:40:23.487648", "return_date": null, "status": "active"}
```

### POST /loans (dispositivo ya prestado) → `409 Conflict`
```json
{"detail": "El dispositivo 'Laptop Lenovo ThinkPad' no está disponible actualmente"}
```

### GET /loans/details (EV10 — join completo con datos anidados)
```json
{
  "loan_id": 1,
  "status": "active",
  "loan_date": "2026-09-17T02:40:23.487648",
  "return_date": null,
  "user": {"id": 1, "name": "Ana Pérez", "email": "ana@sena.edu.co"},
  "device": {"id": 1, "name": "Laptop Lenovo ThinkPad", "serial_number": "LEN-2024-001", "device_type": "laptop"}
}
```

### PATCH /loans/1/return (EV10) → `200 OK`
```json
{"id": 1, "user_id": 1, "device_id": 1, "loan_date": "2026-09-17T02:40:23.487648", "return_date": "2026-09-17T02:40:23.542536", "status": "returned"}
```
*(el dispositivo asociado vuelve automáticamente a `is_available: true`)*

### PATCH /loans/1/return de nuevo (ya devuelto) → `409 Conflict`
```json
{"detail": "Este préstamo ya había sido devuelto anteriormente"}
```

---

## 🔌 Explicación del uso de `Depends()` (Dependency Injection)

El proyecto define 4 dependencias en `app/dependencies/user_dependencies.py`, más una equivalente para dispositivos (`get_device_or_404` en `device_routes.py`):

| Dependencia | Qué valida | Dónde se usa |
|---|---|---|
| `get_user_or_404(user_id)` | Busca el usuario por su path parameter; lanza 404 si no existe | `GET`, `PUT`, `PATCH`, `DELETE` de `/users` por ID, y `GET /users/{id}/loans` |
| `get_device_or_404(device_id)` | Equivalente para dispositivos (EV10) | `GET`, `PUT`, `PATCH`, `DELETE` de `/devices` por ID, y `GET /devices/{id}/loans` |
| `validar_patch_no_vacio(datos)` | Verifica que el body del PATCH tenga al menos un campo distinto de `None` | `PATCH /users/{user_id}` |
| `verificar_api_key(x_api_key)` | Simula autenticación leyendo la cabecera `X-API-Key` | `DELETE /users/{user_id}` |
| `obtener_configuracion_api()` | Expone el nombre y versión de la app (dependencia sin parámetros) | `GET /` |

La ventaja principal: **`get_user_or_404` se declara una sola vez** y se reutiliza en 5 endpoints distintos. Sin `Depends()`, cada uno tendría que repetir la misma búsqueda + el mismo `if usuario is None: raise HTTPException(...)`.

> **Nota técnica:** la guía también sugiere dependencias para "validar correo duplicado" y "validar rol permitido". El rol ya queda cubierto automáticamente por Pydantic (el `Enum` del schema rechaza cualquier valor fuera de `admin/support/user` con un 422, sin código adicional). El correo duplicado sí se valida como lógica de negocio (`user_service.obtener_usuario_por_email()`), pero se invoca directamente desde las rutas en vez de como una dependencia `Depends()` separada: convertirla en dependencia recibiendo el mismo modelo Pydantic del body que ya recibe el propio endpoint hace que FastAPI interprete que hay *dos* cuerpos distintos y exija el JSON anidado en dos claves, rompiendo la petición plana que envía un cliente normal. Se priorizó una implementación simple y funcionalmente correcta sobre forzar ese patrón. Por la misma razón, la validación de disponibilidad de un dispositivo en `POST /loans` (que necesita cruzar `user_service` y `device_service`) se resuelve directamente en la ruta, no como dependencia.

---

## ⚠️ Explicación del manejo de errores implementado

Se usa `HTTPException` en varios escenarios distintos, con el código HTTP que corresponde según el tipo de problema:

1. **Recurso no encontrado** (404) — usuario, dispositivo o préstamo inexistente; en `get_user_or_404` / `get_device_or_404`, y verificado explícitamente en `loan_routes.py`.
2. **Dato duplicado** (400) — correo de usuario duplicado (`POST`/`PUT`/`PATCH` de `/users`), número de serie duplicado (`POST`/`PUT` de `/devices`).
3. **PATCH sin ningún campo enviado** (400) — validado por la dependencia `validar_patch_no_vacio`.
4. **Autorización faltante en DELETE de usuarios** (401) — validado por `verificar_api_key`.
5. **Regla de negocio incumplida** (409 Conflict, EV10) — dos casos: intentar prestar un dispositivo que ya está prestado, e intentar devolver un préstamo que ya fue devuelto. Se usa 409 (no 400) porque el dato en sí es válido — el problema es el *estado actual* del recurso, que entra en conflicto con la operación solicitada.

Pydantic maneja automáticamente un sexto caso: **datos inválidos** (422) — nombre muy corto, correo mal formado, rol fuera de `admin/support/user`, o un campo faltante en el body.

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

**Ejecución de `alembic init` (EV10):**
![Alembic init](images/ev10_1_alembic_init.png)

**Creación de migración con `alembic revision --autogenerate` (EV10):**
![Alembic revision](images/ev10_2_alembic_revision.png)

**Aplicación de la migración con `alembic upgrade head` (EV10):**
![Alembic upgrade](images/ev10_3_alembic_upgrade.png)

**Estructura de tablas generadas — `users`, `devices`, `loans`, `alembic_version` (EV10):**
![Estructura de tablas](images/ev10_4_estructura_tablas.png)

**Swagger UI — creación de usuario, dispositivo y préstamo (EV10):**
![Creación de usuario, dispositivo y préstamo](images/ev10_5_creacion_recursos.png)

**Evidencia de consulta con joins — GET /loans/details (EV10):**
![Consulta con joins](images/ev10_6_joins.png)

**Evidencia de filtros aplicados — GET /loans?device_type=... (EV10):**
![Filtros aplicados](images/ev10_7_filtros.png)

**Evidencia de devolución de dispositivo — PATCH /loans/{id}/return (EV10):**
![Devolución de dispositivo](images/ev10_8_devolucion.png)

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
      ├── feature/documentacion-ev09              (EV09 — README v3)
      └── device_systems_alembic_relaciones       (EV10 — nombre de rama exigido por la guía;
                                                    incluye modelos Device/Loan, relaciones,
                                                    schemas, CRUD de devices, gestión de
                                                    préstamos, consultas con joins, Alembic
                                                    y documentación, todo en varios commits
                                                    dentro de esta misma rama)
```

Cada feature (EV07-EV09) se desarrolló en su propia rama y se integró a `develop` con un merge commit (`--no-ff`). Para EV10, la guía exige explícitamente una única rama llamada `device_systems_alembic_relaciones` que se unifica con `main` al finalizar — por eso todo el trabajo de EV10 vive ahí, en varios commits internos, en vez de dividirse en más ramas `feature/*`. `develop` se fusionó en `main` en cada entrega: **v1.0.0** (EV07), **v2.0.0** (EV08), **v2.1.0** (EV09), **v3.0.0** (EV10). Ninguna rama se elimina tras el merge, para conservar visible el historial completo de cómo se construyó cada versión.

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

### Sobre migraciones, relaciones y consultas avanzadas (EV10)

Antes de usar Alembic, cualquier cambio al esquema (agregar una tabla, una columna) significaba borrar la base de datos y dejar que `create_all()` la regenerara desde cero — funcional en desarrollo, pero completamente inviable en un sistema con datos reales: nadie puede darse el lujo de borrar la base de datos de producción para agregarle una columna. Trabajar con migraciones me hizo entender que el esquema de una base de datos tiene una *historia*, igual que el código tiene un historial de commits, y que esa historia debería poder aplicarse (o revertirse) de forma controlada y repetible en cualquier ambiente.

Implementar las relaciones entre `User`, `Device` y `Loan` también cambió mi forma de pensar los datos relacionados: antes de esto, para saber "qué dispositivos tiene prestados un usuario" habría escrito manualmente una consulta filtrando la tabla de préstamos. Con `relationship()` y `back_populates`, esa navegación (`usuario.loans`, `prestamo.device.name`) se siente casi como acceder a un atributo normal de un objeto Python, aunque por debajo SQLAlchemy esté generando el `JOIN` correspondiente. Eso sí, entendí que esa comodidad no reemplaza saber cuándo escribir un `JOIN` explícito: para las consultas que necesitaba filtrar por columnas de otra tabla (`GET /loans?device_type=laptop`, que filtra por una columna de `devices`, no de `loans`), tuve que construir el `.join()` manualmente en `loan_service.py` — la relación ORM no sustituye la necesidad de saber cómo funciona un `JOIN` en SQL.

Por último, la regla de negocio "un dispositivo prestado no puede volver a prestarse" me hizo valorar la diferencia entre un error de *validación* (422, el dato está mal formado) y un error de *conflicto* (409, el dato es válido pero el estado actual del sistema no permite la operación). Antes agrupaba mentalmente todos los "errores esperados" en una sola categoría; ahora entiendo que el código HTTP correcto comunica *por qué* falló algo, no solo que falló.

## 👤 Autor

Proyecto desarrollado por **Maicol Esneider** como evidencia de aprendizaje de las actividades *Fundamentos de FastAPI* (EV07), *FastAPI Intermedio: Evolución con CRUD Completo* (EV08), *FastAPI con SQLAlchemy: Persistencia de Datos* (EV09) y *FastAPI Avanzado: Migraciones con Alembic, Asociaciones de Modelos y Consultas con Joins* (EV10).