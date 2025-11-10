
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


USER_DATABASE: dict[str, str] = {
    "harry_potter": "Auror",
    "percy_weasley": "Funcionario",
    "hermione_granger": "Ministro",
    "admin": "Ministro" # Un usuario 'admin' genérico
}

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
        user_role = user.level

        user_permissions = self._roles_map.get(user_role, set())

        has_perm = required_permission in user_permissions

        self._log.debug(
            f"Chequeo de Permiso: Usuario='{user.username}' (Rol='{user_role}') | "
            f"Requiere='{required_permission}' | "
            f"Resultado={'CONCEDIDO' if has_perm else 'DENEGADO'}"
        )

        return has_perm

    def check_permission(self, user: User, required_level: str) -> bool:
        # Lógica de permisos (simplificada)
        levels = {"Funcionario": 1, "Auror": 2, "Ministro": 3}
        user_lvl = levels.get(user.level, 0)
        req_lvl = levels.get(required_level, 0)

        return user_lvl >= req_lvl

    # --- ¡ESTE ES EL MÉTODO QUE FALTABA! ---
    def get_permissions_for_role(self, role_name: str) -> set[str]:
        """
        Devuelve el conjunto de permisos para un rol específico.
        """
        # Devuelve una copia para evitar modificaciones externas
        return self._roles_map.get(role_name, set()).copy()


# from domain import Hechizo  # (Import real)

# ... (Clases AuditLogger y AuthService sin cambios) ...

# --- Nuevo Contenedor IoC / Factory de Hechizos ---

class SpellRegistry:
    """
    Actúa como un Contenedor IoC y una Factory para los objetos Hechizo.
    (Versión modificada para ser insensible a mayúsculas/minúsculas)
    """

    def __init__(self):
        # Ahora 'Hechizo' está definido gracias a la importación
        self._spells: dict[str, Type[Hechizo]] = {}
        self._instances: dict[str, Hechizo] = {}

    def register(self, name: str, spell_class: Type[Hechizo]):
        """Registra una *clase* de hechizo (convirtiendo a minúsculas)."""
        key = name.lower()  # <-- ¡CAMBIO!
        if key in self._spells:
            raise ValueError(f"El hechizo '{name}' ya está registrado.")

        self._spells[key] = spell_class
        print(f"Hechizo '{name}' (clave: {key}) registrado en el contenedor IoC.")

    def get_spell(self, name: str) -> Hechizo:
        """
        Obtiene una *instancia* de un hechizo (buscando en minúsculas).
        Implementa el patrón Factory.
        """
        key = name.lower()  # <-- ¡CAMBIO!
        spell_class = self._spells.get(key)  # <-- ¡CAMBIO!

        if not spell_class:
            # Ahora 'SpellNotFoundError' está definido
            raise SpellNotFoundError(f"Hechizo '{name}' no encontrado.")

        return spell_class()