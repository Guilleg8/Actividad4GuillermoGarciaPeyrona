
from pydantic import BaseModel
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Modelo Pydantic (para validación de API)
class SpellRequest(BaseModel):
    spell_name: str
    incantation: str

# Modelo de Dominio (lógica interna)
@dataclass
class User:
    username: str
    level: str  # Ej: "Auror", "Funcionario"


# --- (Contenido anterior: SpellRequest, User) ---
from pydantic import BaseModel
from dataclasses import dataclass



# ... (Clases User y SpellRequest sin cambios) ...

# --- Nuevas Excepciones de Dominio ---

class SpellNotFoundError(Exception):
    """Lanzada cuando un hechizo no se encuentra en el registro."""
    pass


class UnforgivableSpellError(Exception):
    """Lanzada cuando se intenta usar un hechizo imperdonable."""

    def __init__(self, spell_name: str, username: str):
        self.spell_name = spell_name
        self.username = username
        super().__init__(
            f"¡Uso ilegal de Hechizo Imperdonable '{spell_name}' "
            f"detectado por {username}!"
        )

class PermissionDeniedError(Exception):
    """Lanzada por el aspecto de seguridad cuando falta un permiso."""
    def __init__(self, username: str, required_permission: str):
        self.username = username
        self.required_permission = required_permission
        super().__init__(
            f"El usuario '{username}' no tiene el permiso requerido: "
            f"'{required_permission}'"
        )
# --- Nuevas Clases de Hechizos (Lógica de Negocio) ---

class Hechizo(ABC):
    """Interfaz abstracta para todos los hechizos."""

    @abstractmethod
    def execute(self, user: User, **kwargs) -> str:
        """
        Ejecuta la lógica de negocio pura del hechizo.
        Devuelve un string con el resultado.
        """
        pass


class Lumos(Hechizo):
    """Implementación concreta del hechizo Lumos."""

    def execute(self, user: User, **kwargs) -> str:
        # Lógica de negocio pura
        print(f"LÓGICA DE NEGOCIO: {user.username} enciende su varita.")
        return "¡Luz encendida! (Lumos)"


class ExpectoPatronum(Hechizo):
    """Implementación concreta de Expecto Patronum."""

    def execute(self, user: User, **kwargs) -> str:
        # Lógica de negocio pura
        print(f"LÓGICA DE NEGOCIO: {user.username} conjura un Patronus.")
        return "Patronus conjurado para defensa."


# app/domain.py

# ... (tus otras clases: Hechizo, Lumos, ExpectoPatronum) ...

class AvadaKedavra(Hechizo):
    """
    Implementación de un hechizo imperdonable.
    Solo el rol 'Ministro' (admin) tiene autorización para ejecutarlo.
    """

    def execute(self, user: User, **kwargs) -> str:
        # --- ¡ESTA ES LA NUEVA LÓGICA DE SEGURIDAD! ---
        # 1. Comprueba si el rol del usuario NO es 'Ministro'.
        if user.level != "Ministro":
            print(f"LÓGICA DE NEGOCIO: ¡ACCESO DENEGADO! {user.username} (Rol: {user.level}) "
                  f"intentó lanzar Avada Kedavra.")

            # 2. Lanza el error (esto lo verá el usuario en el dashboard).
            raise UnforgivableSpellError(
                spell_name="Avada Kedavra",
                username=user.username
            )

        # 3. Si llegamos aquí, el usuario ES un "Ministro" (admin).
        print(f"LÓGICA DE NEGOCIO: {user.username} (Rol: Ministro) "
              f"ha ejecutado Avada Kedavra (Autorización de Admin).")

        # 4. Simulación de la ejecución "exitosa" (solo para el admin).
        return "Hechizo Imperdonable ejecutado con Autorización del Ministerio."

class LoginRequest(BaseModel):
    """El cuerpo (body) esperado para la petición de login."""
    username: str