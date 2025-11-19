import logging
import time
import os
import re
import random
import json
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app

from app.config_logging import setup_logging
from app.domain import (
    User, SpellRequest, LoginRequest,
    PermissionDeniedError, UnforgivableSpellError, SpellNotFoundError
)
from app.services import AuditLogger, AuthService, SpellRegistry, USER_DATABASE
from app.dependencies import (
    get_current_user, get_audit_logger, get_auth_service, get_spell_registry, NotAuthenticatedError
)
from app.aspects import log_audit, require_permission
from app.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUESTS_LATENCY

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
FRONTEND_DIR = APP_DIR / "frontend"
LOGS_DIR = PROJECT_ROOT / "logs"
AUDIT_LOG_FILE = LOGS_DIR / "ministry_audit.log"

setup_logging()

app = FastAPI(
    title="Ministerio de Magia - Sistema de Gestión",
    description="API para la gestión de hechizos y eventos mágicos."
)
log = logging.getLogger("app.main")


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


@app.exception_handler(NotAuthenticatedError)
async def not_authenticated_handler(request: Request, exc: NotAuthenticatedError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "No autenticado. Por favor, inicie sesión."},
    )


@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    log.warning(f"Fallo de permisos: {exc}")
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})


@app.exception_handler(UnforgivableSpellError)
async def unforgivable_spell_handler(request: Request, exc: UnforgivableSpellError):
    log.error(f"¡HECHIZO IMPERDONABLE! {exc}")
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


@app.exception_handler(SpellNotFoundError)
async def spell_not_found_handler(request: Request, exc: SpellNotFoundError):
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})



@app.post("/api/login", summary="Valida un usuario y devuelve su rol")
def api_login(login_data: LoginRequest):
    username_lower = login_data.username.lower()
    role = USER_DATABASE.get(username_lower)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nombre de usuario no encontrado."
        )
    return {"username": username_lower, "role": role}


@app.get("/api/user-info")
def get_user_info(
        current_user: User = Depends(get_current_user),
        auth: AuthService = Depends(get_auth_service)
):
    role = current_user.level
    permissions = auth.get_permissions_for_role(role)
    return {
        "username": current_user.username,
        "role": role,
        "permissions": list(permissions)
    }


@app.post("/hechizos/lanzar", status_code=status.HTTP_201_CREATED, operation_id="cast_spell")
@log_audit(action_name="Lanzar Hechizo")
@require_permission(permission="spell:cast")
def cast_spell(
        spell: SpellRequest,
        current_user: User = Depends(get_current_user),
        audit: AuditLogger = Depends(get_audit_logger),
        auth: AuthService = Depends(get_auth_service),
        spell_registry: SpellRegistry = Depends(get_spell_registry)
):
    log.debug(f"Lógica de endpoint: lanzando '{spell.spell_name}'")
    hechizo_obj = spell_registry.get_spell(spell.spell_name)
    result_message = hechizo_obj.execute(user=current_user, incantation=spell.incantation)
    return {"message": result_message, "user": current_user.username}


def _parse_audit_log() -> dict:
    spell_counts = {}
    if not os.path.exists(AUDIT_LOG_FILE):
        return {}
    try:
        with open(AUDIT_LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                status_match = re.search(r"'status': '(\w+)'", line)
                spell_match = re.search(r"'hechizo': '([\w\s]+)'", line)

                if status_match and spell_match:
                    status = status_match.group(1)
                    spell_name = spell_match.group(1)

                    if spell_name not in spell_counts:
                        spell_counts[spell_name] = {"INTENTO": 0, "ÉXITO": 0, "FALLO": 0}

                    if status in spell_counts[spell_name]:
                        spell_counts[spell_name][status] += 1
    except Exception as e:
        log.error(f"Error leyendo log: {e}")
        return {"error": str(e)}
    return spell_counts


def _get_performance_metrics() -> dict:
    avg_latency = random.uniform(0.05, 0.25)
    events_per_sec = random.randint(10, 100)
    return {
        "current_latency_ms": round(avg_latency * 1000, 2),
        "events_per_second": events_per_sec,
    }


@app.get("/api/dashboard-data")
def get_dashboard_data():
    return {
        "table": _parse_audit_log(),
        "chart": _get_performance_metrics()
    }



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


if __name__ == "__main__":
    import uvicorn

    log.info("Iniciando servidor Uvicorn...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)