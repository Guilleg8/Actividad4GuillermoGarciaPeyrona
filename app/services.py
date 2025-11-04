
import logging
from typing import Type
from app.domain import User, Hechizo, SpellNotFoundError

# Obtenemos el logger de auditoría configurado en dictConfig
audit_logger = logging.getLogger("app.audit")

class AuditLogger:
    """
    Servicio de Auditoría.
    En un sistema real, esto escribiría en una BD o un sistema de logs.
    """
    def log(self, user: User, action: str, details: dict):
        # Usamos el logger de auditoría configurado
        audit_logger.info(f"Usuario: {user.username} | Acción: {action} | Detalles: {details}")

class AuthService:
    """
    Servicio de Seguridad.
    Verifica los permisos del usuario.
    """
    def check_permission(self, user: User, required_level: str) -> bool:
        # Lógica de permisos (simplificada)
        levels = {"Funcionario": 1, "Auror": 2, "Ministro": 3}
        user_lvl = levels.get(user.level, 0)
        req_lvl = levels.get(required_level, 0)

        return user_lvl >= req_lvl


ROLES_TO_PERMISSIONS: dict[str, set[str]] = {
    "Funcionario": {
        "spell:read",
        "log:read",
    },
    "Auror": {
        "spell:read",
        "log:read",
        "spell:cast",  # <-- Permiso granular
        "archive:read",
    },
    "JefeDeDepartamento": {
        "spell:read",
        "log:read",
        "spell:cast",
        "archive:read",
        "archive:write",
        "user:manage_interns",
    },
    "Ministro": {
        "spell:read",
        "log:read",
        "spell:cast",
        "archive:read",
        "archive:write",
        "user:manage_interns",
        "user:admin",  # <-- Permiso de super-admin
        "system:config",
    }
}


class AuthService:
    """
    Servicio de Seguridad (Modificado).
    Verifica permisos granulares basados en el rol del usuario.
    """

    def __init__(self, roles_map: dict[str, set[str]]):
        self._roles_map = roles_map
        self._log = logging.getLogger("app.auth_service")
        self._log.info("Servicio de Autenticación (con permisos) inicializado.")

    def has_permission(self, user: User, required_permission: str) -> bool:
        """
        Verifica si el rol del usuario tiene asignado el permiso requerido.
        """
        user_role = user.level  # Usamos 'level' como el 'rol'

        # Obtenemos los permisos para el rol del usuario.
        # .get(user_role, set()) devuelve un set vacío si el rol no existe.
        user_permissions = self._roles_map.get(user_role, set())

        has_perm = required_permission in user_permissions

        self._log.debug(
            f"Chequeo de Permiso: Usuario='{user.username}' (Rol='{user_role}') | "
            f"Requiere='{required_permission}' | "
            f"Resultado={'CONCEDIDO' if has_perm else 'DENEGADO'}"
        )

        return has_perm
# --- (Contenido anterior: logging, AuditLogger, AuthService) ---
import logging


# from domain import Hechizo  # (Import real)

# ... (Clases AuditLogger y AuthService sin cambios) ...

# --- Nuevo Contenedor IoC / Factory de Hechizos ---

class SpellRegistry:
    """
    Actúa como un Contenedor IoC y una Factory para los objetos Hechizo.

    Mantiene un registro de clases de hechizos y crea instancias
    cuando se le solicita.
    """

    def __init__(self):
        self._spells: dict[str, Type[Hechizo]] = {}
        self._instances: dict[str, Hechizo] = {}

    def register(self, name: str, spell_class: Type[Hechizo]):
        """Registra una *clase* de hechizo."""
        if name in self._spells:
            raise ValueError(f"El hechizo '{name}' ya está registrado.")
        self._spells[name] = spell_class
        print(f"Hechizo '{name}' registrado en el contenedor IoC.")

    def get_spell(self, name: str) -> Hechizo:
        """
        Obtiene una *instancia* de un hechizo.
        Implementa el patrón Factory.
        """
        spell_class = self._spells.get(name)
        if not spell_class:
            raise SpellNotFoundError(f"Hechizo '{name}' no encontrado.")

        # Para este ejemplo, creamos una nueva instancia cada vez.
        # Podríamos implementar un patrón Singleton aquí si fuera necesario.
        return spell_class()