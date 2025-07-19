import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.log_handler import LogHandler

log_handler = LogHandler()

class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = None
        try:
            response = await call_next(request)
            duration = (time.time() - start_time) * 1000  # ms
            log_handler.log_performance_metric(
                metric_name=f"API_{request.url.path}_latency",
                value=duration,
                unit="ms"
            )
            return response
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_handler.log_performance_metric(
                metric_name=f"API_{request.url.path}_exception",
                value=duration,
                unit="ms"
            )
            raise e 