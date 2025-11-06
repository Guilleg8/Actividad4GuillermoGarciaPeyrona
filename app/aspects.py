# app/aspects.py

import functools
import logging
import time  # <--- ¡AQUÍ ESTÁ LA LÍNEA QUE FALTABA!
from typing import Callable, Any

# --- Imports necesarios para los aspectos ---
from app.services import AuditLogger, AuthService
from app.domain import User, PermissionDeniedError
from app.metrics import (
    SPELL_CAST_COUNTER,
    SPELL_CAST_LATENCY,
    EVENT_COUNTER
)

# --- Logger para los propios aspectos ---
log = logging.getLogger("app.aspects")
log.info("Módulo de Aspectos (AOP) cargado.")


# --- Función Auxiliar ---

def _get_deps_from_kwargs(kwargs: dict) -> tuple:
    """
    Función auxiliar para extraer dependencias clave (inyectadas por FastAPI)
    desde los argumentos de la función decorada.
    """
    current_user: User | None = kwargs.get('current_user')
    audit: AuditLogger | None = kwargs.get('audit')
    auth: AuthService | None = kwargs.get('auth')

    if not current_user:
        log.warning("Aspecto ejecutado sin 'current_user' en kwargs.")
        current_user = User(username="Sistema", level="Sistema")

    return current_user, audit, auth


# --- Aspecto 1: Auditoría (@around) ---

def log_audit(action_name: str) -> Callable:
    """
    Aspecto (decorador) para la auditoría Y MÉTRICAS de negocio.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # 'time' ahora está definido gracias al import
            start_time = time.monotonic()  # Iniciar temporizador

            user, audit_service, _ = _get_deps_from_kwargs(kwargs)

            # (El primer argumento suele ser el body)
            request_body = args[0] if args else kwargs.get('spell')

            spell_name = "unknown"
            if request_body and hasattr(request_body, 'spell_name'):
                spell_name = request_body.spell_name
            # Para el /test-audit, el body es None, así que le damos un nombre
            elif action_name == "PruebaDeAuditoria":
                spell_name = "PruebaDeAuditoria"

            details = {"peticion": str(request_body)}

            if not audit_service:
                log.error(f"Aspecto 'log_audit' no pudo encontrar 'AuditLogger' para la acción: {action_name}")
                return func(*args, **kwargs)

            log.debug(f"ASPECTO (Audit): Registrando INTENTO para '{action_name}'")
            audit_service.log(user, action_name, {"status": "INTENTO", **details})

            try:
                # 2. Ejecutar la lógica de negocio (la función original)
                result = func(*args, **kwargs)
                latency = time.monotonic() - start_time

                # 3. Lógica "Después" (Éxito)
                log.debug(f"ASPECTO (Audit): Registrando ÉXITO para '{action_name}'")
                audit_service.log(user, action_name, {"status": "ÉXITO", **details})

                # --- ¡ACTUALIZAR MÉTRICAS (Éxito)! ---
                SPELL_CAST_LATENCY.labels(spell_name=spell_name, status='success').observe(latency)
                SPELL_CAST_COUNTER.labels(spell_name=spell_name, status='success').inc()
                EVENT_COUNTER.labels(event_type='spell_success').inc()

                return result

            except Exception as e:
                latency = time.monotonic() - start_time

                # 4. Lógica "Después" (Fallo)
                log.debug(f"ASPECTO (Audit): Registrando FALLO para '{action_name}'")
                details["error"] = str(e)
                audit_service.log(user, action_name, {"status": "FALLO", **details})

                status_label = 'fail_security' if isinstance(e, PermissionDeniedError) else 'fail_logic'
                event_label = 'security_fail' if isinstance(e, PermissionDeniedError) else 'spell_fail'

                # --- ¡ACTUALIZAR MÉTRICAS (Fallo)! ---
                SPELL_CAST_LATENCY.labels(spell_name=spell_name, status=status_label).observe(latency)
                SPELL_CAST_COUNTER.labels(spell_name=spell_name, status=status_label).inc()
                EVENT_COUNTER.labels(event_type=event_label).inc()

                raise e

        return wrapper

    return decorator


# --- Aspecto 2: Seguridad (@before) ---

def require_permission(permission: str) -> Callable:
    """
    Aspecto (decorador) para la seguridad.
    Verifica si el usuario tiene un PERMISO específico.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # 1. Lógica "Antes" (Verificación)
            user, _, auth_service = _get_deps_from_kwargs(kwargs)

            if not auth_service:
                log.error(f"Aspecto 'require_permission' no pudo encontrar 'AuthService'. Denegando por defecto.")
                raise PermissionDeniedError(user.username, "Servicio de Auth no disponible")

            log.debug(f"ASPECTO (Security): Verificando permiso '{permission}' para '{user.username}'")

            if not auth_service.has_permission(user, permission):
                log.warning(
                    f"ASPECTO (Security): ¡ACCESO DENEGADO! "
                    f"Usuario: {user.username}, Permiso Requerido: {permission}"
                )
                raise PermissionDeniedError(user.username, permission)

            log.debug(f"ASPECTO (Security): Acceso concedido.")

            # 2. Ejecutar la lógica de negocio (si el permiso es válido)
            return func(*args, **kwargs)

        return wrapper

    return decorator