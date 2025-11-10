from app.services import (
    AuditLogger,
    AuthService,
    SpellRegistry,
    ROLES_TO_PERMISSIONS
)
from app.domain import (
    User,
    Lumos,
    ExpectoPatronum,
    AvadaKedavra
)
from fastapi import Request, Depends, HTTPException, status # <-- ¡Importa Request!

_audit_service_instance = AuditLogger()
_auth_service_instance = AuthService(roles_map=ROLES_TO_PERMISSIONS)

def get_audit_logger() -> AuditLogger:
    """Dependencia: Obtiene el servicio de auditoría."""
    return _audit_service_instance

def get_auth_service() -> AuthService:
    """Dependencia: Obtiene el servicio de autenticación."""
    return _auth_service_instance



# --- (Contenido anterior: AuditLogger, AuthService, get_...) ---
# from services import AuditLogger, AuthService, SpellRegistry # (Import real)
# from domain import Lumos, ExpectoPatronum, AvadaKedavra   # (Import real)

# ... (Instancias y funciones 'get' de Audit y Auth sin cambios) ...

# --- Configuración del Contenedor de Hechizos ---

def create_spell_registry() -> SpellRegistry:
    """
    Crea y configura la instancia del registro de hechizos.
    Esto se ejecuta una sola vez al inicio de la aplicación.
    """
    registry = SpellRegistry()

    # Aquí registramos todos nuestros hechizos (Inversión de Control)
    registry.register("Lumos", Lumos)
    registry.register("Expecto Patronum", ExpectoPatronum)
    registry.register("Avada Kedavra", AvadaKedavra)

    return registry


# Instancia Singleton de nuestro contenedor IoC
_spell_registry_instance = create_spell_registry()


def get_spell_registry() -> SpellRegistry:
    """Dependencia: Obtiene el registro de hechizos."""
    return _spell_registry_instance


class NotAuthenticatedError(Exception):
    """Lanzada cuando el usuario no está autenticado (falta de headers)."""
    pass


# --- ¡VERSIÓN MODIFICADA DE get_current_user! ---
def get_current_user(request: Request) -> User:
    """
    Dependencia: Obtiene el usuario desde los headers HTTP.

    El frontend (JS) es responsable de añadir estos headers
    leyéndolos desde el localStorage.
    """
    username = request.headers.get("X-User-Username")
    role = request.headers.get("X-User-Role")

    if not username or not role:
        # Si faltan los headers, el usuario no está "logeado"
        raise NotAuthenticatedError("No se proporcionaron cabeceras de autenticación.")

    return User(username=username, level=role)