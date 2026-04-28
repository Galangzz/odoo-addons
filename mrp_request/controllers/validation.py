from odoo import http
from odoo.exceptions import ValidationError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

STATE_MRP = ['draft', 'confirmed', 'progress', 'to_close', 'done', 'cancel']
class ValidationController(http.Controller):

    def sanitize_payload_report_manufacturing_order(self, fields) :
        _logger.info('check_validation_report_manufacturing_order')
        company_id = fields.get('company_id') or False
        product_id = fields.get('product_id') or False
        date_start = fields.get('date_start') or False
        date_end = fields.get('date_end') or False
        limit = fields.get('limit') or False
        offset = fields.get('offset') or False
        state = fields.get('state') or False
        
        company_id = self.check_int(company_id, 'company_id')
        product_id = self.check_int(product_id, 'product_id')
        date_start = self.check_null(date_start, 'date_start')
        date_end = self.check_null(date_end, 'date_end')
        limit = self.check_int(limit, 'limit')
        offset = self.check_int(offset, 'offset')
        
        if state not in STATE_MRP:
            raise ValidationResponseError(message=f'{state} is not a valid state \n valid states are [{STATE_MRP}]', fields=state, http_status=400)
        sanitize_fields = {}
        
        if company_id:
            sanitize_fields.update({'company_id': company_id})
        if product_id:
            sanitize_fields.update({'product_id': product_id})
        if date_start and date_end:
            date_start = self.sanitize_date_format(date_start, 'date_start')
            date_end = self.sanitize_date_format(date_end, 'date_end')
            self.sanitize_date_start_end(date_start, date_end)
            sanitize_fields.update({'date_start': date_start})
            sanitize_fields.update({'date_end': date_end})
        if limit:
            sanitize_fields.update({'limit': limit})
        if offset:
            sanitize_fields.update({'offset': offset})
        if state:
            sanitize_fields.update({'state': state})
        
        return sanitize_fields
        

    def check_int(self, value, name):
        if not value:
            return value
        sanitize_value = value
        if isinstance(value, int):
            if self.int_positive(value):
                sanitize_value = int(value)
            else:
                raise ValidationResponseError(message=f'{name} is not a positive integer', fields=name, http_status=400)
        elif isinstance(value, str) and value.isdigit():
            value = value.strip()
            value = int(value)
            if self.int_positive(value):
                sanitize_value = int(value)
            else:
                raise ValidationResponseError(message=f'{name} is not a positive integer', fields=name, http_status=400)
        else:
            raise ValidationResponseError(message=f'{name} is not a  integer', fields=name, http_status=400)
        
        return sanitize_value
    

    def check_null(self, value, name):
        if not value:
            raise ValidationResponseError(
                message=f'{name} is required', 
                fields=name, 
                http_status=400
            )
        elif isinstance(value, str):            
            return value.strip()
        else:
            return value


    def int_positive(self, value):
        try:
            if not value:
                return False
            if value > 0:
                return True
            else:
                return False
        except ValueError:
            return False
        
    
    def sanitize_date_format(self, value, name):
        try:
            return datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00') if name == 'date_start' else datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d 23:59:59')
        except Exception as e:
            raise ValidationResponseError(
                    message=f"Format {name} '{value}' invalid. Use YYYY-MM-DD",
                    fields={'invalid_field': f'{name}', 'value': value},
                    http_status=400
                )
    
    def sanitize_date_start_end(self, date_start, date_end):
        if date_start and date_end:
            if date_start > date_end:
                raise ValidationResponseError(
                    message='date_start is greater than date_end', 
                    fields={'date_start': date_start, 'date_end': date_end}, 
                    http_status=400
                )

class ValidationResponseError(ValidationError):
    def __init__(self, message, fields, http_status=400):
        super().__init__(message)
        self.message = message
        self.fields = fields
        self.http_status = http_status