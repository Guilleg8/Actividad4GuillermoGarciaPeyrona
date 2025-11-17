# 🧙‍♂️ Sistema de Gestión Mágico - Ministerio de Magia

Este proyecto es una aplicación web completa (backend y frontend) que simula un Sistema de Gestión Mágico para el Ministerio de Magia.

El núcleo del proyecto es una API de **FastAPI** (Python) construida sobre principios de diseño de software avanzados, incluyendo **Programación Orientada a Aspectos (AOP)** e **Inyección de Dependencias (DI)**, para crear una arquitectura modular, segura y fácil de mantener.

El frontend es un **Dashboard interactivo** de una sola página (SPA) que permite a los usuarios iniciar sesión, ver datos y ejecutar acciones mágicas basadas en sus permisos.

## Características Principales

* **Backend con FastAPI:** Un servidor API moderno, rápido y asíncrono.
* **Programación Orientada a Aspectos (AOP):** Lógica transversal (seguridad, auditoría, métricas) implementada con decoradores (`@log_audit`, `@require_permission`) que mantienen la lógica de negocio limpia.
* **Inyección de Dependencias (DI):** Uso de `fastapi.Depends` para inyectar servicios (`AuthService`, `SpellRegistry`) en los endpoints.
* **Sistema de Roles y Permisos (RBAC):** Un sistema de autenticación simulado donde los usuarios tienen roles (`Ministro`, `Auror`, `Funcionario`) y los endpoints requieren permisos granulares (`spell:cast`).
* **Auditoría Automática:** Cada intento de lanzar un hechizo (exitoso o fallido) se registra automáticamente en un archivo `logs/ministry_audit.log`.
* **Lógica de Negocio Aislada:** Lógica de hechizos (como la regla de `Avada Kedavra` [fuente: `app/domain.py`]) está aislada en clases de dominio, desacoplada de la API.
* **Dashboard Interactivo:** Un frontend que incluye:
    * Página de inicio de sesión (`/`).
    * Dashboard protegido (`/dashboard`).
    * Vista de Perfil de Usuario y Permisos.
    * Gráfico de Rendimiento del Sistema (simulado).
    * Tabla de Auditoría de Eventos (leída desde el log).
    * Formulario para Lanzar Hechizos (que respeta los permisos).
* **Métricas:** Integración básica con `prometheus-client` para definir métricas (`SPELL_CAST_COUNTER`, `SPELL_CAST_LATENCY`) [fuente: `app/metrics.py`].

## Arquitectura

La arquitectura está diseñada para ser **modular** y **desacoplada**:

* **`domain.py`**: Contiene la lógica de negocio pura y los modelos de datos (ej. `class Lumos(Hechizo)`). No sabe nada sobre la web o las bases de datos.
* **`services.py`**: Contiene los servicios que definen los roles (`ROLES_TO_PERMISSIONS`) y la "base de datos" de usuarios (`USER_DATABASE`).
* **`aspects.py`**: Implementa la AOP. Contiene los decoradores que envuelven la lógica de negocio para añadir seguridad y auditoría.
* **`dependencies.py`**: Define cómo se crean e inyectan los servicios (`get_current_user`, `get_auth_service`).
* **`main.py`**: Es la capa de API (controlador). Define los endpoints HTTP, los conecta con los decoradores de aspectos y las dependencias, y sirve el frontend estático.
* **`frontend/`**: Contiene la capa de presentación (HTML/CSS/JS), completamente separada del backend.

## Estructura del Proyecto
```
Actividad4GuillermoGarciaPeyrona/
├── app/
│   ├── frontend/
│   │   ├── app.js            # Lógica del Dashboard
│   │   ├── index.html        # HTML del Dashboard
│   │   ├── login.css         # Estilos del Login
│   │   ├── login.html        # HTML del Login
│   │   ├── login.js          # Lógica del Login
│   │   └── style.css         # Estilos del Dashboard
│   ├── __init__.py
│   ├── aspects.py            # Decoradores AOP (Seguridad, Auditoría)
│   ├── config_logging.py     # Configuración de logging
│   ├── dependencies.py       # Inyección de Dependencias
│   ├── domain.py             # Lógica de Negocio Pura (Hechizos)
│   ├── main.py               # Servidor FastAPI y Endpoints
│   ├── metrics.py            # Definiciones de Prometheus
│   └── services.py           # Lógica de Servicios (Roles, Usuarios)
├── logs/
│   └── ministry_audit.log    # Archivo de auditoría
└── requirements.txt          # Dependencias del proyecto
```

## Instalación

1.  **Clonar el repositorio (si es necesario):**
    ```bash
    git clone [https://github.com/tu-usuario/Actividad4GuillermoGarciaPeyrona.git](https://github.com/tu-usuario/Actividad4GuillermoGarciaPeyrona.git)
    cd Actividad4GuillermoGarciaPeyrona
    ```

2.  **Crear un entorno virtual:**
    ```bash
    python -m venv .venv
    ```

3.  **Activar el entorno virtual:**
    * En Windows: `.\.venv\Scripts\activate`
    * En macOS/Linux: `source .venv/bin/activate`

4.  **Instalar las dependencias:**
    Crea un archivo `requirements.txt` (o reemplaza el existente [fuente: `requirements.txt`]) con este contenido (que es el correcto para el proyecto final):
    ```txt
    fastapi
    uvicorn[standard]
    prometheus-client
    aiofiles
    ```
    Luego, instálalo:
    ```bash
    pip install -r requirements.txt
    ```

## Ejecución

1.  Asegúrate de estar en la carpeta raíz del proyecto (`Actividad4GuillermoGarciaPeyrona/`).
2.  Ejecuta el servidor Uvicorn apuntando a la aplicación dentro de la carpeta `app`:

    ```bash
    uvicorn app.main:app --reload
    ```

3.  El servidor se iniciará en `http://127.0.0.1:8000`.

## Modo de Uso

1.  Abre tu navegador y ve a **`http://localhost:8000/`**.
2.  Serás recibido por la página de inicio de sesión.
3.  Puedes usar los siguientes usuarios (definidos en `app/services.py`):
    * `harry_potter` (Rol: Auror, puede lanzar hechizos normales)
    * `admin` (Rol: Ministro, puede lanzar `Avada Kedavra`)
    * `percy_weasley` (Rol: Funcionario, no puede lanzar hechizos)
4.  Inicia sesión y serás redirigido al dashboard principal (`/dashboard`).
5.  Explora las tarjetas:
    * **Perfil de Usuario:** Muestra quién eres y qué permisos tienes.
    * **Lanzar Hechizo:** Prueba a lanzar "Lumos" o "Avada Kedavra" para ver la lógica de permisos y la tabla de auditoría en acción.
    * **Auditoría:** Observa cómo se actualiza la tabla en tiempo real cada vez que lanzas un hechizo.
    * **Cerrar Sesión:** Haz clic para volver a la página de login.
