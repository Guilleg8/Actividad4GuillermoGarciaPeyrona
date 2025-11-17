
import functools
import logging
import time
from typing import Callable

from app.services import AuditLogger, AuthService
from app.domain import User, PermissionDeniedError
from app.metrics import (
    SPELL_CAST_COUNTER,
    SPELL_CAST_LATENCY,
    EVENT_COUNTER
)

log = logging.getLogger("app.aspects")
log.info("Módulo de Aspectos (AOP) cargado.")


def _get_deps_from_kwargs(kwargs: dict) -> tuple:
    current_user: User | None = kwargs.get('current_user')
    audit: AuditLogger | None = kwargs.get('audit')
    auth: AuthService | None = kwargs.get('auth')

    if not current_user:
        log.warning("Aspecto ejecutado sin 'current_user' en kwargs.")
        current_user = User(username="Sistema", level="Sistema")

    return current_user, audit, auth


def log_audit(action_name: str) -> Callable:

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            start_time = time.monotonic()

            user, audit_service, _ = _get_deps_from_kwargs(kwargs)

            request_body = args[0] if args else kwargs.get('spell')

            spell_name = "unknown"
            if request_body and hasattr(request_body, 'spell_name'):
                spell_name = request_body.spell_name
            elif action_name == "PruebaDeAuditoria":
                spell_name = "PruebaDeAuditoria"

            details = {
                "peticion": str(request_body),
                "hechizo": spell_name
            }

            if not audit_service:
                log.error(f"Aspecto 'log_audit' no pudo encontrar 'AuditLogger'...")
                return func(*args, **kwargs)

            audit_service.log(user, action_name, {"status": "INTENTO", **details})

            try:
                result = func(*args, **kwargs)
                latency = time.monotonic() - start_time

                audit_service.log(user, action_name, {"status": "ÉXITO", **details})

                SPELL_CAST_LATENCY.labels(spell_name=spell_name, status='success').observe(latency)
                SPELL_CAST_COUNTER.labels(spell_name=spell_name, status='success').inc()
                EVENT_COUNTER.labels(event_type='spell_success').inc()

                return result

            except Exception as e:
                latency = time.monotonic() - start_time

                details["error"] = str(e)
                audit_service.log(user, action_name, {"status": "FALLO", **details})

                status_label = 'fail_security' if isinstance(e, PermissionDeniedError) else 'fail_logic'
                event_label = 'security_fail' if isinstance(e, PermissionDeniedError) else 'spell_fail'

                SPELL_CAST_LATENCY.labels(spell_name=spell_name, status=status_label).observe(latency)
                SPELL_CAST_COUNTER.labels(spell_name=spell_name, status=status_label).inc()
                EVENT_COUNTER.labels(event_type=event_label).inc()

                raise e

        return wrapper

    return decorator


def require_permission(permission: str) -> Callable:

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

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

            return func(*args, **kwargs)

        return wrapper

    return decorator