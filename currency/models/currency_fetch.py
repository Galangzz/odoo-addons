from odoo import models, fields, api
from datetime import datetime, timedelta
import requests
import logging
import xml.etree.ElementTree as ET
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

class CurrencyFetch(models.Model):
    _inherit = 'res.currency'

    def _get_default_from_date(self):
        return fields.Date.today() - timedelta(days=7)


    from_date = fields.Date('From Date', required=True, default=_get_default_from_date)
    to_date = fields.Date('To Date', required=True, default=fields.Date.context_today)
    is_company_idr_id = fields.Boolean(compute='_compute_is_company_idr_id')
    
    
    @api.depends_context('company')
    def _compute_is_company_idr_id(self):
        for currency in self:
            _logger.info("Company ID: %s", self.env.company.currency_id)
            currency.is_company_idr_id = self.env.company.currency_id.name == 'IDR'

    @api.constrains('from_date', 'to_date')
    def _check_date_range(self):
        for rec in self:
            if rec.to_date < rec.from_date:
                raise ValidationError(_('To Date must be greater than From Date'))
    
    def fetch_currency_bi(self):
        
        if not self._compute_is_company_idr_id:
            return
        
        url = "https://www.bi.go.id/biwebservice/wskursbi.asmx/getSubKursLokal3"
        headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/237.84.2.178 Safari/537.36'
        }
        for rec in self:
            params = {
                'mts': rec.name,
                'startdate': rec.from_date,
                'enddate': rec.to_date
            }
            
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    params=params,
                    timeout=100, 
                    )
                root = ET.fromstring(response.content)
                ns = {'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1'}
                tables = root.findall('.//Table', ns)
                data_kurs = []

                for table in tables:
                    item = {
                        'id': table.findtext('id_subkurslokal'),
                        'currency_id': rec.id,
                        'rate': 1/((float(table.findtext('beli_subkurslokal'))+ float(table.findtext('jual_subkurslokal')))/2),
                        'name': table.findtext('tgl_subkurslokal').split('T')[0]
                    }
                    data_kurs.append(item)
                if len(data_kurs) == 0:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Info'),
                            'message': _('Data not found'),
                            'sticky': False,
                            'type': 'info', 
                        }
                    }
                    
                sanitize_data = self._sanitize_data_create(datas=data_kurs)
                if len(sanitize_data) == 0:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Info'),
                            'message': _('Data already exists'),
                            'sticky': False,
                            'type': 'info', 
                        }
                    }

                self.env['res.currency.rate'].create(sanitize_data)
                return {
                    'type': 'ir.actions.client',
                        'tag': 'reload',
                        'params': {
                            'title': _('Success'),
                            'message': _('Data fetched successfully'),
                            'sticky': False,
                            'type': 'success', 
                        }
                    }
            except Exception as e:
                if isinstance(e, requests.exceptions.RequestException):
                    _logger.error(e.response)
                    raise ValidationError(_('Failed to fetch currency from BI'))
                else:
                    _logger.error(e)

    @api.depends('from_date', 'to_date')
    def _compute_start_date(self):
        for record in self:
            record.from_date =  record.to_date - timedelta(days=7)
            
    @api.model
    def _sanitize_data_create(self, datas):
        sanitize_data = []
        for data in datas:
            if self.env['res.currency.rate'].search([('name', '=', data['name']), ('currency_id', '=', data['currency_id'])]):
                continue
            else:
                sanitize_data.append(data)
        return sanitize_data
