"""FastAPI middleware that auto-tracks in-flight requests for Prometheus."""
from starlette.middleware.base import BaseHTTPMiddleware
from monitoring.prometheus_metrics import active_connections


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        active_connections.inc()
        try:
            response = await call_next(request)
        finally:
            active_connections.dec()
        return response
