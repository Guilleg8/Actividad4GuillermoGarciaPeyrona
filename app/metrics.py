from prometheus_client import Counter, Histogram

SPELL_CAST_COUNTER = Counter(
    "magic_spell_casts_total",
    "Contador total de hechizos lanzados",
    ["spell_name", "status"]
)

SPELL_CAST_LATENCY = Histogram(
    "magic_spell_cast_latency_seconds",
    "Latencia de ejecución de hechizos (en segundos)",
    ["spell_name", "status"]
)

EVENT_COUNTER = Counter(
    "magic_events_total",
    "Contador de eventos mágicos (incluye fallos de seguridad)",
    ["event_type"]
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Contador total de peticiones HTTP",
    ["method", "path", "status_code"]
)

HTTP_REQUESTS_LATENCY = Histogram(
    "http_requests_latency_seconds",
    "Latencia de peticiones HTTP (en segundos)",
    ["method", "path"]
)

print("Módulo de Métricas (Prometheus) cargado.")