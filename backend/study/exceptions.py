from django.db import OperationalError, IntegrityError
from rest_framework.views import exception_handler
from rest_framework.response import Response

def api_exception_handler(exc,context):
    result=exception_handler(exc,context)
    if result is not None:return result
    if isinstance(exc,OperationalError):
        return Response({'detail':'The database is temporarily unavailable. Retry the same request; completed submissions will not be duplicated.'},status=503)
    if isinstance(exc,IntegrityError):
        return Response({'detail':'This operation conflicted with another request. Refresh and retry.'},status=409)
    return result
