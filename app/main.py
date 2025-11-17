import logging
import time
import re
import random
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from pathlib import Path

from app.config_logging import setup_logging
from app.domain import (
    User, SpellRequest, PermissionDeniedError, UnforgivableSpellError, SpellNotFoundError
)
from app.services import AuditLogger, AuthService, SpellRegistry
from app.dependencies import (
    get_current_user, get_audit_logger, get_auth_service, get_spell_registry, NotAuthenticatedError
)
from app.domain import LoginRequest
from app.services import USER_DATABASE
from app.aspects import log_audit, require_permission
from app.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUESTS_LATENCY
from prometheus_client import make_asgi_app


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
FRONTEND_DIR = APP_DIR / "frontend"
LOGS_DIR = PROJECT_ROOT / "logs"

setup_logging()

app = FastAPI(
    title="Ministerio de Magia - Sistema de Gestión",
    description="API para la gestión de hechizos y eventos mágicos."
)
log = logging.getLogger("app.main")

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", include_in_schema=False)
async def read_login():
    return FileResponse(FRONTEND_DIR / "login.html")

@app.get("/dashboard", include_in_schema=False)
async def read_index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/login", include_in_schema=False)
async def redirect_to_root():
    return FileResponse(FRONTEND_DIR / "login.html")

@app.post(
    "/hechizos/lanzar",
    status_code=status.HTTP_201_CREATED,
    summary="Lanza un hechizo (Protegido por AOP)",
    operation_id="cast_spell"
)
@log_audit(action_name="Lanzar Hechizo")
@require_permission(permission="spell:cast")
def cast_spell(
        spell: SpellRequest,
        current_user: User = Depends(get_current_user),
        spell_registry: SpellRegistry = Depends(get_spell_registry)
):

    log.debug(f"Lógica de endpoint: obteniendo '{spell.spell_name}' del registro.")

    hechizo_obj = spell_registry.get_spell(spell.spell_name)

    result_message = hechizo_obj.execute(
        user=current_user,
        incantation=spell.incantation
    )

    log.debug("Lógica de endpoint: hechizo ejecutado, devolviendo respuesta.")

    return {
        "message": result_message,
        "user": current_user.username
    }

@app.post("/hechizos/lanzar", status_code=status.HTTP_201_CREATED)
def cast_spell(
            spell: SpellRequest,

            current_user: User = Depends(get_current_user),
            audit: AuditLogger = Depends(get_audit_logger),
            auth: AuthService = Depends(get_auth_service),

            spell_registry: SpellRegistry = Depends(get_spell_registry)
    ):

        log.debug(f"Usuario '{current_user.username}' intenta lanzar '{spell.spell_name}'")

        required_level = "Auror"
        if not auth.check_permission(current_user, required_level):
            log.warning(f"Fallo de seguridad: {current_user.username} no tiene nivel {required_level}")
            audit.log(current_user, "Lanzar Hechizo", {"status": "FALLO_PERMISO", "hechizo": spell.spell_name})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes el nivel de {required_level} requerido."
            )

        try:

            log.debug(f"Consultando el Contenedor IoC para '{spell.spell_name}'")
            hechizo_obj = spell_registry.get_spell(spell.spell_name)

            result_message = hechizo_obj.execute(
                user=current_user,
                incantation=spell.incantation
            )

            audit.log(current_user, "Lanzar Hechizo", {"status": "ÉXITO", "hechizo": spell.spell_name})

            return {
                "message": result_message,
                "user": current_user.username
            }

        except SpellNotFoundError as e:
            log.info(f"Intento de lanzar hechizo desconocido: {spell.spell_name}")
            audit.log(current_user, "Lanzar Hechizo", {"status": "FALLO_NO_ENCONTRADO", "hechizo": spell.spell_name})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except UnforgivableSpellError as e:
            log.error(f"¡ALERTA! {e}")
            audit.log(current_user, "VIOLACIÓN MÁGICA GRAVE", {"status": "IMPERDONABLE", "error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"¡ALERTA DE SEGURIDAD! {e}"
            )
        except Exception as e:
            log.error(f"Error inesperado al ejecutar el hechizo: {e}")
            audit.log(current_user, "Lanzar Hechizo", {"status": "FALLO_INESPERADO", "error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del Ministerio."
            )
@app.middleware("http")
async def track_http_metrics(request: Request, call_next):
    start_time = time.monotonic()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        latency = time.monotonic() - start_time
        path = request.url.path
        if path != "/metrics":
            log.debug(f"Middleware Métricas: {request.method} {path} -> {status_code} en {latency:.4f}s")
            HTTP_REQUESTS_LATENCY.labels(method=request.method, path=path).observe(latency)
            HTTP_REQUESTS_TOTAL.labels(method=request.method, path=path, status_code=status_code).inc()
    return response

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    log.warning(f"Fallo de permisos (manejador): {exc.username} necesita '{exc.required_permission}'")
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})

@app.exception_handler(UnforgivableSpellError)
async def unforgivable_spell_handler(request: Request, exc: UnforgivableSpellError):
    log.error(f"¡HECHIZO IMPERDONABLE DETECTADO (manejador)! {exc}")
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": f"¡ALERTA DE SEGURIDAD MÁGICA! {exc}"})

@app.exception_handler(SpellNotFoundError)
async def spell_not_found_handler(request: Request, exc: SpellNotFoundError):
    log.info(f"Hechizo no encontrado (manejador): {exc}")
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.post(
    "/hechizos/lanzar",
    status_code=status.HTTP_201_CREATED,
    summary="Lanza un hechizo (Protegido por AOP)"
)

@log_audit(action_name="Lanzar Hechizo")
@require_permission(permission="spell:cast")
def cast_spell(
        spell: SpellRequest,

        current_user: User = Depends(get_current_user),
        spell_registry: SpellRegistry = Depends(get_spell_registry)
):

    log.debug(f"Lógica de endpoint: obteniendo '{spell.spell_name}' del registro.")

    hechizo_obj = spell_registry.get_spell(spell.spell_name)

    result_message = hechizo_obj.execute(
        user=current_user,
        incantation=spell.incantation
    )

    log.debug("Lógica de endpoint: hechizo ejecutado, devolviendo respuesta.")

    return {
        "message": result_message,
        "user": current_user.username
    }

AUDIT_LOG_FILE = LOGS_DIR / "ministry_audit.log"


@app.get("/api/dashboard-data", summary="Datos para el Dashboard del Ministerio")
def get_dashboard_data():

    table_data = _parse_audit_log()

    chart_data = _get_performance_metrics()

    return {
        "table": table_data,
        "chart": chart_data
    }


def _parse_audit_log() -> dict:

    log.debug(f"Leyendo archivo de log: {AUDIT_LOG_FILE}")
    spell_counts = {}

    try:
        with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:

                status_match = re.search(r"'status': '(\w+)'", line)

                spell_match = re.search(r"'hechizo': '([\w\s]+)'", line)

                spell_name = "Desconocido"

                if spell_match:
                    spell_name = spell_match.group(1)
                elif "PruebaDeAuditoria" in line:
                    spell_name = "PruebaDeAuditoria"
                else:
                    continue

                if status_match:
                    status = status_match.group(1)

                    if spell_name not in spell_counts:
                        spell_counts[spell_name] = {"INTENTO": 0, "ÉXITO": 0, "FALLO": 0}

                    if status == "INTENTO":
                        spell_counts[spell_name]["INTENTO"] += 1
                    elif status == "ÉXITO":
                        spell_counts[spell_name]["ÉXITO"] += 1
                    elif status == "FALLO":
                        spell_counts[spell_name]["FALLO"] += 1

    except FileNotFoundError:
        log.warning(f"El archivo de auditoría {AUDIT_LOG_FILE} no se encontró.")
        return {"error": "Log no encontrado"}
    except Exception as e:
        log.error(f"Error parseando el log de auditoría: {e}")
        return {"error": str(e)}

    return spell_counts


def _parse_audit_log() -> dict:
    log.debug(f"Leyendo archivo de log: {AUDIT_LOG_FILE}")
    spell_counts = {}
    try:
        with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if "status" not in line: continue
                status_match = re.search(r"'status': '(\w+)'", line)
                spell_match = re.search(r"'hechizo': '([\w\s]+)'", line)
                if spell_match and status_match:
                    spell_name = spell_match.group(1)
                    status = status_match.group(1)
                    if spell_name not in spell_counts:
                        spell_counts[spell_name] = {"ÉXITO": 0, "FALLO": 0, "INTENTO": 0}
                    if status in spell_counts[spell_name]:
                        spell_counts[spell_name][status] += 1
    except FileNotFoundError:
        log.warning(f"El archivo de auditoría {AUDIT_LOG_FILE} no se encontró.")
        return {"error": "Log no encontrado"}
    except Exception as e:
        log.error(f"Error parseando el log de auditoría: {e}")
        return {"error": str(e)}
    return spell_counts
AUDIT_LOG_FILE = LOGS_DIR / "ministry_audit.log"


def _get_performance_metrics() -> dict:

    avg_latency = random.uniform(0.05, 0.25)
    events_per_sec = random.randint(10, 100)

    return {
        "current_latency_ms": round(avg_latency * 1000, 2),
        "events_per_second": events_per_sec,
    }

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.exception_handler(NotAuthenticatedError)
async def not_authenticated_handler(request: Request, exc: NotAuthenticatedError):
    log.warning(f"Intento de acceso no autenticado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "No autenticado. Por favor, inicie sesión."},
    )

@app.get("/", include_in_schema=False)
async def read_index():
    return FileResponse(FRONTEND_DIR / "index.html")
if __name__ == "__main__":
    import uvicorn
    log.info("Iniciando servidor Uvicorn en modo desarrollo...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


@app.post("/api/login", summary="Valida un usuario y devuelve su rol")
def api_login(
        login_data: LoginRequest
):

    username_lower = login_data.username.lower()

    role = USER_DATABASE.get(username_lower)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nombre de usuario no encontrado en los registros del Ministerio."
        )

    return {
        "username": username_lower,
        "role": role
    }

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", include_in_schema=False)
async def read_index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/login", include_in_schema=False)
async def read_login():
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/api/user-info", summary="Obtiene la info del usuario actual")
def get_user_info(
        current_user: User = Depends(get_current_user),
        auth: AuthService = Depends(get_auth_service)
):

    role = current_user.level

    permissions = auth.get_permissions_for_role(role)

    return {
        "username": current_user.username,
        "role": role,
        "permissions": list(permissions)  # Convertimos el 'set' a 'list' para JSON
    }