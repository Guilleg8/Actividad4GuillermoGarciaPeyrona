# --- (Contenido anterior) ---
import logging
import logging.config
import sys
import os
# ¡NUEVO!
from jsonlogging import JsonFormatter



def setup_logging():
    """Configura el sistema de logging (modificado para logs JSON)."""

    LOG_DIR = "logs"
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print(f"Directorio de logs creado en: {LOG_DIR}")

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,

        # --- Formateadores (Modificado) ---
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
            'audit': {
                'format': 'AUDIT | %(asctime)s | %(message)s',
            },
            # --- NUEVO FORMATTER ESTRUCTURADO ---
            'json': {
                'class': 'jsonlogging.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
            },
        },

        # --- Handlers (Modificado) ---
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': sys.stdout,
            },
            'audit_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'audit',
                'filename': os.path.join(LOG_DIR, 'ministry_audit.log'),
                'maxBytes': 10485760, 'backupCount': 5,
            },
            # --- NUEVO HANDLER ESTRUCTURADO ---
            'json_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'json',  # Usa el formatter JSON
                'filename': os.path.join(LOG_DIR, 'app_structured.log.json'),
                'maxBytes': 10485760, 'backupCount': 5,
            },
        },

        # --- Loggers (Modificado) ---
        'loggers': {
            '': {
                'handlers': ['console', 'json_file'],  # Log raíz a consola y JSON
                'level': 'INFO',
            },
            'app.main': {
                'level': 'DEBUG',
                'propagate': True,
            },
            'app.aspects': {
                'level': 'DEBUG',
                'propagate': True,
            },
            'app.audit': {
                'level': 'INFO',
                'propagate': False,
                'handlers': ['audit_file'],  # El log de auditoría va por separado
            }
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)
    print("Configuración de Logging cargada (con JSON estructurado).")