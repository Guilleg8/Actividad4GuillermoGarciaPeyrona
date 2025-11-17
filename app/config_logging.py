import logging
import logging.config
import sys
import os
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CONFIG_DIR.parent
LOG_DIR = PROJECT_ROOT / "logs"

def setup_logging():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print(f"Directorio de logs creado en: {LOG_DIR}")

    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            },
            'audit': {
                'format': 'AUDIT | %(asctime)s | %(message)s',
            },
        },

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
                'maxBytes': 10485760,
                'backupCount': 5,
                'encoding': 'utf-8',
            },
        },

        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'INFO',
            },
            'app.main': {'level': 'DEBUG', 'propagate': True, },
            'app.aspects': {'level': 'DEBUG', 'propagate': True, },
            'app.audit': {
                'level': 'INFO',
                'propagate': False,
                'handlers': ['audit_file'],
            }
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)
    print("Configuración de Logging cargada.")