from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        error_code = exc.__class__.__name__.upper()
        detail = response.data
        response.data = {
            "error": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            "code": error_code,
            "detail": detail,
        }
    return response
