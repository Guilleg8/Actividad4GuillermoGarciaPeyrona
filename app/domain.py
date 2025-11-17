from pydantic import BaseModel
from dataclasses import dataclass
from abc import ABC, abstractmethod

class SpellRequest(BaseModel):
    spell_name: str
    incantation: str

@dataclass
class User:
    username: str
    level: str

from pydantic import BaseModel

class SpellNotFoundError(Exception):
    pass

class UnforgivableSpellError(Exception):

    def __init__(self, spell_name: str, username: str):
        self.spell_name = spell_name
        self.username = username
        super().__init__(
            f"¡Uso ilegal de Hechizo Imperdonable '{spell_name}' "
            f"detectado por {username}!"
        )

class PermissionDeniedError(Exception):
    def __init__(self, username: str, required_permission: str):
        self.username = username
        self.required_permission = required_permission
        super().__init__(
            f"El usuario '{username}' no tiene el permiso requerido: "
            f"'{required_permission}'"
        )

class Hechizo(ABC):

    @abstractmethod
    def execute(self, user: User, **kwargs) -> str:

        pass


class Lumos(Hechizo):

    def execute(self, user: User, **kwargs) -> str:
        print(f"LÓGICA DE NEGOCIO: {user.username} enciende su varita.")
        return "¡Luz encendida! (Lumos)"


class ExpectoPatronum(Hechizo):
    def execute(self, user: User, **kwargs) -> str:
        print(f"LÓGICA DE NEGOCIO: {user.username} conjura un Patronus.")
        return "Patronus conjurado para defensa."

class AvadaKedavra(Hechizo):
    def execute(self, user: User, **kwargs) -> str:
        if user.level != "Ministro":
            print(f"LÓGICA DE NEGOCIO: ¡ACCESO DENEGADO! {user.username} (Rol: {user.level}) "
                  f"intentó lanzar Avada Kedavra.")
            raise UnforgivableSpellError(
                spell_name="Avada Kedavra",
                username=user.username
            )

        print(f"LÓGICA DE NEGOCIO: {user.username} (Rol: Ministro) "
              f"ha ejecutado Avada Kedavra (Autorización de Admin).")

        return "Hechizo Imperdonable ejecutado con Autorización del Ministerio."

class LoginRequest(BaseModel):
    username: str