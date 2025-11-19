import logging
from typing import Type
from app.domain import User, Hechizo, SpellNotFoundError

USER_DATABASE: dict[str, str] = {
    "harry_potter": "Auror",
    "percy_weasley": "Funcionario",
    "hermione_granger": "Ministro",
    "admin": "Ministro"
}

ROLES_TO_PERMISSIONS: dict[str, set[str]] = {
    "Funcionario": {
        "spell:read",
        "log:read",
    },
    "Auror": {
        "spell:read",
        "log:read",
        "spell:cast",
        "archive:read",
    },
    "Ministro": {
        "spell:read",
        "log:read",
        "spell:cast",
        "archive:read",
        "archive:write",
        "user:manage_interns",
        "user:admin",
        "system:config",
    }
}

audit_logger = logging.getLogger("app.audit")


class AuditLogger:
    def log(self, user: User, action: str, details: dict):
        audit_logger.info(f"Usuario: {user.username} | Acción: {action} | Detalles: {details}")


class AuthService:
    def __init__(self, roles_map: dict[str, set[str]]):
        self._roles_map = roles_map
        self._log = logging.getLogger("app.auth_service")
        self._log.info("Servicio de Autenticación (con permisos) inicializado.")

    def has_permission(self, user: User, required_permission: str) -> bool:
        user_role = user.level
        user_permissions = self._roles_map.get(user_role, set())
        has_perm = required_permission in user_permissions

        self._log.debug(
            f"Chequeo de Permiso: Usuario='{user.username}' (Rol='{user_role}') | "
            f"Requiere='{required_permission}' | "
            f"Resultado={'CONCEDIDO' if has_perm else 'DENEGADO'}"
        )
        return has_perm

    def get_permissions_for_role(self, role_name: str) -> set[str]:
        return self._roles_map.get(role_name, set()).copy()


class SpellRegistry:
    def __init__(self):
        self._spells: dict[str, Type[Hechizo]] = {}

    def register(self, name: str, spell_class: Type[Hechizo]):
        key = name.lower()
        if key in self._spells:
            raise ValueError(f"El hechizo '{name}' ya está registrado.")
        self._spells[key] = spell_class
        print(f"Hechizo '{name}' (clave: {key}) registrado en el contenedor IoC.")

    def get_spell(self, name: str) -> Hechizo:
        key = name.lower()
        spell_class = self._spells.get(key)
        if not spell_class:
            raise SpellNotFoundError(f"Hechizo '{name}' no encontrado.")
        return spell_class()