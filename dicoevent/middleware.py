import time
from loguru import logger

class LoggingMiddleware:
    """
    Middleware that logs incoming HTTP requests, response status codes,
    latency, and unhandled errors using Loguru.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        user_info = request.user.username if getattr(request, 'user', None) and request.user.is_authenticated else 'Anonymous'

        response = self.get_response(request)

        duration = (time.time() - start_time) * 1000
        status_code = response.status_code

        log_message = (
            f"{request.method} {request.get_full_path()} - "
            f"Status: {status_code} - "
            f"User: {user_info} - "
            f"Duration: {duration:.2f}ms"
        )

        if status_code >= 500:
            logger.error(log_message)
        elif status_code >= 400:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return response

    def process_exception(self, request, exception):
        user_info = request.user.username if getattr(request, 'user', None) and request.user.is_authenticated else 'Anonymous'
        logger.exception(
            f"Unhandled exception on {request.method} {request.get_full_path()} "
            f"by {user_info}: {str(exception)}"
        )
        return None
