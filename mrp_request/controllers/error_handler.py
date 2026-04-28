from odoo.http import request
from odoo.addons.mrp_request.controllers.validation import ValidationResponseError #type: ignore
import logging
from functools import wraps

_logger = logging.getLogger(__name__)


def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            if isinstance(error, ValidationResponseError):
                return request.make_json_response(
                    data={
                        'status': error.http_status,
                        'success': False,
                        'fields': error.fields,
                        'message': error.message,
                        'data': []
                    },
                    status=error.http_status
                )
                
            return request.make_json_response(
                status=500,
                data={
                    'status': 500,
                    'success': False,
                    'message': str(error.__repr__()),
                }
            )
    return wrapper