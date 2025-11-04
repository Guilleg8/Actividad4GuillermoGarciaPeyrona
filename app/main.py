
from fastapi import FastAPI, Depends, HTTPException, status, Request
import logging
from app.dependencies import (
    get_current_user,
    get_audit_logger,
    get_auth_service,
    get_spell_registry
)
from app.domain import (
    User,
    SpellRequest,  # <-- Esta es la importación que faltaba
    UnforgivableSpellError,
    SpellNotFoundError
)
from app.services import AuditLogger, AuthService, SpellRegistry
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Ministerio de Magia - Sistema de Gestión",
    description="API para la gestión de hechizos y eventos mágicos."
)

log = logging.getLogger("app.main")

# --- ¡NUEVO! Configurar CORS ---
# Esto permite que el archivo HTML llame a la API desde el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permitir todos los orígenes (para demo)
    allow_credentials=True,
    allow_methods=["*"], # Permitir todos los métodos
    allow_headers=["*"],
)# Permitir todos los headers

# --- Endpoint principal demostrando DI ---

@app.post("/hechizos/lanzar", status_code=status.HTTP_201_CREATED)
def cast_spell(
        spell: SpellRequest,

        # === INYECCIÓN DE DEPENDENCIAS (DI) ===
        # FastAPI inyecta automáticamente las dependencias aquí.
        # El endpoint NO sabe cómo se crean, solo los usa.

        current_user: User = Depends(get_current_user),
        audit: AuditLogger = Depends(get_audit_logger),
        auth: AuthService = Depends(get_auth_service)
    ):


        log.debug(f"Usuario '{current_user.username}' intenta lanzar '{spell.spell_name}'")

        # --- Lógica de negocio MEZCLADA con preocupaciones transversales ---
        # (Esto es lo que mejoraremos con AOP en el siguiente paso)

        # 1. Preocupación: Seguridad (Autorización)
        required_level = "Auror"
        if not auth.check_permission(current_user, required_level):
            log.warning(f"Fallo de seguridad: {current_user.username} no tiene nivel {required_level}")
            # 2. Preocupación: Auditoría (del fallo)
            audit.log(current_user, "Lanzar Hechizo", {"status": "FALLO_PERMISO", "hechizo": spell.spell_name})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes el nivel de {required_level} requerido."
            )

        # 3. Lógica de Negocio (El Núcleo)
        log.info(f"Lanzando hechizo: {spell.incantation}!")
        # ... (Aquí iría la lógica real de negocio) ...

        audit.log(current_user, "Lanzar Hechizo", {"status": "ÉXITO", "hechizo": spell.spell_name})

        return {
            "message": f"¡{spell.incantation} lanzado con éxito!",
            "user": current_user.username
        }


@app.post("/hechizos/lanzar", status_code=status.HTTP_201_CREATED)
def cast_spell(
            spell: SpellRequest,

            # === INYECCIÓN DE DEPENDENCIAS (DI) ===
            current_user: User = Depends(get_current_user),
            audit: AuditLogger = Depends(get_audit_logger),
            auth: AuthService = Depends(get_auth_service),

            # Nueva dependencia: inyectamos nuestro contenedor IoC
            spell_registry: SpellRegistry = Depends(get_spell_registry)
    ):
        """
        Endpoint para lanzar un hechizo.
        Usa el Contenedor IoC (SpellRegistry) para obtener la lógica de negocio.
        """
        log.debug(f"Usuario '{current_user.username}' intenta lanzar '{spell.spell_name}'")

        # --- Preocupaciones Transversales (AÚN PRESENTES) ---
        # (Esto es lo que limpiaremos en el siguiente paso con AOP)

        # 1. Seguridad (Autorización)
        required_level = "Auror"
        if not auth.check_permission(current_user, required_level):
            log.warning(f"Fallo de seguridad: {current_user.username} no tiene nivel {required_level}")
            audit.log(current_user, "Lanzar Hechizo", {"status": "FALLO_PERMISO", "hechizo": spell.spell_name})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes el nivel de {required_level} requerido."
            )

        try:
            # --- Lógica de Negocio (Abstraída) ---

            # 2. Obtenemos el objeto de negocio desde el Contenedor IoC
            log.debug(f"Consultando el Contenedor IoC para '{spell.spell_name}'")
            hechizo_obj = spell_registry.get_spell(spell.spell_name)

            # 3. Ejecutamos la lógica de negocio pura
            # El endpoint no sabe NADA sobre Lumos o Avada Kedavra,
            # solo sabe ejecutar la interfaz Hechizo.
            result_message = hechizo_obj.execute(
                user=current_user,
                incantation=spell.incantation
            )

            # 4. Auditoría (del éxito)
            audit.log(current_user, "Lanzar Hechizo", {"status": "ÉXITO", "hechizo": spell.spell_name})

            return {
                "message": result_message,
                "user": current_user.username
            }

        # --- Manejo de Excepciones de Dominio ---

        except SpellNotFoundError as e:
            log.info(f"Intento de lanzar hechizo desconocido: {spell.spell_name}")
            audit.log(current_user, "Lanzar Hechizo", {"status": "FALLO_NO_ENCONTRADO", "hechizo": spell.spell_name})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except UnforgivableSpellError as e:
            log.error(f"¡ALERTA! {e}")
            # Auditoría de alta prioridad
            audit.log(current_user, "VIOLACIÓN MÁGICA GRAVE", {"status": "IMPERDONABLE", "error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"¡ALERTA DE SEGURIDAD! {e}"
            )
        except Exception as e:
            # Captura de cualquier otro error de negocio
            log.error(f"Error inesperado al ejecutar el hechizo: {e}")
            audit.log(current_user, "Lanzar Hechizo", {"status": "FALLO_INESPERADO", "error": str(e)})
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del Ministerio."
            )

# --- Punto de entrada para Uvicorn (para ejecutar el archivo) ---
if __name__ == "__main__":
    import uvicorn
    # (Esto es solo para desarrollo. En producción se usa un Gunicorn + Uvicorn)
    log.info("Iniciando servidor Uvicorn en modo desarrollo...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    # --- (Contenido anterior: FastAPI, Depends, etc.) ---
    from fastapi import FastAPI, Depends, HTTPException, status
    import logging

