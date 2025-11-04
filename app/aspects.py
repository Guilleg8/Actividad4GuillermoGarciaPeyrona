import functools
import logging
from typing import Callable, Any


# Importamos los servicios y modelos que los aspectos necesitarán
# (En una app real, estos se importarían desde .services y .domain)
# from services import AuditLogger, AuthService
# from domain import User

# --- Excepciones personalizadas para los Aspectos ---
# (Podemos moverlas a domain.py si se prefiere)

class PermissionDeniedError(Exception):
    """Lanzada por el aspecto de seguridad."""

    def __init__(self, username: str, required_level: str):
        self.username = username
        self.required_level = required_level
        super().__init__(
            f"El usuario {username} no tiene el nivel "
            f"requerido: {required_level}"
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
        # Asignamos un usuario 'Sistema' para que los logs no fallen
        current_user = User(username="Sistema", level="Sistema")

    return current_user, audit, auth


# --- Aspecto 1: Auditoría (@around) ---


# ... (Función _get_deps_from_kwargs sin cambios) ...

# --- Aspecto 1: Auditoría (@around) MODIFICADO ---

def log_audit(action_name: str) -> Callable:
    """
    Aspecto (decorador) para la auditoría Y MÉTRICAS de negocio.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            start_time = time.monotonic()  # Iniciar temporizador

            user, audit_service, _ = _get_deps_from_kwargs(kwargs)
            request_body = args[0] if args else kwargs.get('spell')

            # Intentamos obtener el nombre del hechizo para las métricas
            spell_name = "unknown"
            if hasattr(request_body, 'spell_name'):
                spell_name = request_body.spell_name

            details = {"peticion": str(request_body)}

            if not audit_service:
                log.error(f"Aspecto 'log_audit' no pudo encontrar 'AuditLogger'...")
                # No podemos registrar métricas si el logger falla
                return func(*args, **kwargs)

            log.debug(f"ASPECTO (Audit): Registrando INTENTO para '{action_name}'")
            audit_service.log(user, action_name, {"status": "INTENTO", **details})

            try:
                # 2. Ejecutar la lógica de negocio (la función original)
                result = func(*args, **kwargs)
                latency = time.monotonic() - start_time  # Calcular latencia

                # 3. Lógica "Después" (Éxito)
                log.debug(f"ASPECTO (Audit): Registrando ÉXITO para '{action_name}'")
                audit_service.log(user, action_name, {"status": "ÉXITO", **details})

                # --- ¡ACTUALIZAR MÉTRICAS (Éxito)! ---
                SPELL_CAST_LATENCY.labels(spell_name=spell_name, status='success').observe(latency)
                SPELL_CAST_COUNTER.labels(spell_name=spell_name, status='success').inc()
                EVENT_COUNTER.labels(event_type='spell_success').inc()

                return result

            except Exception as e:
                latency = time.monotonic() - start_time  # Calcular latencia

                # 4. Lógica "Después" (Fallo)
                log.debug(f"ASPECTO (Audit): Registrando FALLO para '{action_name}'")
                details["error"] = str(e)
                audit_service.log(user, action_name, {"status": "FALLO", **details})

                # Determinar el tipo de fallo para la métrica
                status_label = 'fail_security' if isinstance(e, PermissionDeniedError) else 'fail_logic'
                event_label = 'security_fail' if isinstance(e, PermissionDeniedError) else 'spell_fail'

                # --- ¡ACTUALIZAR MÉTRICAS (Fallo)! ---
                SPELL_CAST_LATENCY.labels(spell_name=spell_name, status=status_label).observe(latency)
                SPELL_CAST_COUNTER.labels(spell_name=spell_name, status=status_label).inc()
                EVENT_COUNTER.labels(event_type=event_label).inc()

                raise e

        return wrapper

    return decorator

def require_permission(level: str) -> Callable:
    """
    Aspecto (decorador) para la seguridad.
    Implementa un patrón "@before": se ejecuta ANTES de la lógica.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # 1. Lógica "Antes" (Verificación)
            user, _, auth_service = _get_deps_from_kwargs(kwargs)

            if not auth_service:
                log.error(f"Aspecto 'require_permission' no pudo encontrar 'AuthService'. Denegando por defecto.")
                raise PermissionDeniedError(user.username, "Servicio de Auth no disponible")

            log.debug(f"ASPECTO (Security): Verificando nivel '{level}' para '{user.username}'")

            if not auth_service.check_permission(user, level):
                log.warning(
                    f"ASPECTO (Security): ¡ACCESO DENEGADO! "
                    f"Usuario: {user.username}, Nivel Requerido: {level}"
                )
                # Lanzamos una excepción que el manejador de FastAPI capturará
                raise PermissionDeniedError(user.username, level)

            log.debug(f"ASPECTO (Security): Acceso concedido.")

            # 2. Ejecutar la lógica de negocio (si el permiso es válido)
            return func(*args, **kwargs)

        return wrapper

    return decorator


log = logging.getLogger("app.aspects")


# ... (Función auxiliar _get_deps_from_kwargs sin cambios) ...

# ... (Aspecto log_audit sin cambios) ...


# --- Aspecto 2: Seguridad (@before) MODIFICADO ---

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

            # --- Lógica de Permisos MODIFICADA ---
            # Ya no comparamos niveles, llamamos al nuevo método del servicio.
            if not auth_service.has_permission(user, permission):
                log.warning(
                    f"ASPECTO (Security): ¡ACCESO DENEGADO! "
                    f"Usuario: {user.username}, Permiso Requerido: {permission}"
                )
                # Lanzamos la excepción con el permiso
                raise PermissionDeniedError(user.username, permission)

            log.debug(f"ASPECTO (Security): Acceso concedido.")

            # 2. Ejecutar la lógica de negocio (si el permiso es válido)
            return func(*args, **kwargs)

        return wrapper

    return decorator

# --- Aspecto 3: Transacciones (@around) ---

def manage_transaction() -> Callable:
    """
    Aspecto (decorador) para transacciones.
    Simula un patrón "@around" para commit/rollback.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            # 1. Lógica "Antes" (BEGIN TRANSACTION)
            log.info("ASPECTO (Transaction): Iniciando transacción...")
            # Aquí iría: db.begin()

            try:
                # 2. Ejecutar la lógica de negocio
                result = func(*args, **kwargs)

                # 3. Lógica "Después" (COMMIT)
                log.info("ASPECTO (Transaction): Lógica exitosa. Haciendo COMMIT.")
                # Aquí iría: db.commit()
                return result

            except Exception as e:
                # 4. Lógica "Después" (ROLLBACK)
                log.error(f"ASPECTO (Transaction): Error en lógica. Haciendo ROLLBACK. Error: {e}")
                # Aquí iría: db.rollback()
                raise e  # Re-lanzar para que el log de auditoría lo capture

        return wrapper

    return decorator