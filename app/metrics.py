from prometheus_client import Counter, Histogram

# --- Métricas de Negocio ---
# (Responden a "Resultados esperados")

# 1. Tasa de eventos mágicos procesados por segundo
# (Contador de Hechizos)
SPELL_CAST_COUNTER = Counter(
    "magic_spell_casts_total",
    "Contador total de hechizos lanzados",
    ["spell_name", "status"]  # Labels: 'Lumos', 'success'
)

# 2. Tiempo medio de respuesta de hechizos
# (Histograma de Latencia)
SPELL_CAST_LATENCY = Histogram(
    "magic_spell_cast_latency_seconds",
    "Latencia de ejecución de hechizos (en segundos)",
    ["spell_name", "status"]
)

# 3. Contador general de eventos
EVENT_COUNTER = Counter(
    "magic_events_total",
    "Contador de eventos mágicos (incluye fallos de seguridad)",
    ["event_type"] # Labels: 'spell_success', 'spell_fail', 'security_fail'
)


# --- Métricas de Servicio HTTP (Estándar) ---

# Contador de peticiones HTTP
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Contador total de peticiones HTTP",
    ["method", "path", "status_code"]
)

# Histograma de latencia HTTP
HTTP_REQUESTS_LATENCY = Histogram(
    "http_requests_latency_seconds",
    "Latencia de peticiones HTTP (en segundos)",
    ["method", "path"]
)

print("Módulo de Métricas (Prometheus) cargado.")