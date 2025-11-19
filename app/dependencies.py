from fastapi import Request, HTTPException, status
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

def create_spell_registry() -> SpellRegistry:
    registry = SpellRegistry()
    registry.register("Lumos", Lumos)
    registry.register("Expecto Patronum", ExpectoPatronum)
    registry.register("Avada Kedavra", AvadaKedavra)
    return registry

_spell_registry_instance = create_spell_registry()


def get_audit_logger() -> AuditLogger:
    return _audit_service_instance

def get_auth_service() -> AuthService:
    return _auth_service_instance

def get_spell_registry() -> SpellRegistry:
    return _spell_registry_instance

class NotAuthenticatedError(Exception):
    pass

def get_current_user(request: Request) -> User:

    username = request.headers.get("X-User-Username")
    role = request.headers.get("X-User-Role")

    if not username or not role:
        raise NotAuthenticatedError("No se proporcionaron cabeceras de autenticación.")

    return User(username=username, level=role)