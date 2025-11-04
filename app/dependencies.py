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

_audit_service_instance = AuditLogger()
_auth_service_instance = AuthService(roles_map=ROLES_TO_PERMISSIONS)

def get_audit_logger() -> AuditLogger:
    """Dependencia: Obtiene el servicio de auditoría."""
    return _audit_service_instance

def get_auth_service() -> AuthService:
    """Dependencia: Obtiene el servicio de autenticación."""
    return _auth_service_instance


_auth_service_instance = AuthService(roles_map=ROLES_TO_PERMISSIONS)

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

def get_current_user() -> User:
    """
    Dependencia: Simula la obtención del usuario autenticado.
    En una app real, esto leería un token (ej. OAuth2).
    """
    # Para este ejemplo, simulamos un usuario fijo (Harry).
    return User(username="harry_potter", level="Auror")