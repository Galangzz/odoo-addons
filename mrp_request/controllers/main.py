from datetime import datetime
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError
import xlsxwriter
import io
import logging

_logger = logging.getLogger(__name__)

XLSX_TITLE_HEADER = 'Laporan Siklus Produksi'
STATE_MRP = ['draft', 'confirmed', 'progress', 'to_close', 'done', 'cancel']
class MrpRequest(http.Controller):
    @http.route('/api/odoo/report/manufacturing-order', type='http', auth='user', methods=['POST'], csrf=False)
    def get_product_data_by_date(self):
        
        payload = request.get_json_data()
        _logger.info("Payload is %s", payload)
        
        company_id = payload.get('company_id') or False
        product_id = payload.get('product_id') or False
        date_start = payload.get('date_start') or False
        date_end = payload.get('date_end') or False
        limit = payload.get('limit') or False
        offset = payload.get('offset') or False
        state = payload.get('state') or False
        
        if not date_start or not date_end:
            return request.make_json_response(
                status=400,
                data={
                    'status': 400,
                    'success': False,
                    'error': f'{ValidationError.__name__}',
                    'message': f"{'date_start' if not date_start else 'date_end'} is required"
                }
            )
        
        format_date_start = datetime.strptime(date_start, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')
        format_date_end = datetime.strptime(date_end, '%Y-%m-%d').strftime('%Y-%m-%d 23:59:59')

        company_id_val = int(company_id) if company_id else None
        product_id_val = int(product_id) if product_id else None
        limit_val = int(limit) if limit else None
        offset_val = int(offset) if offset else None
        
        domain = []

        if  company_id_val :
            domain.append(('company_id', '=', company_id_val))
        if  product_id_val:
            domain.append(('product_id', '=', product_id_val))
        if date_start:
            domain.append(('date_start', '>=', format_date_start))
        if date_end:
            domain.append(('date_start', '<=', format_date_end))
        if state:
            if state not in STATE_MRP:            
                return request.make_json_response(
                    status=400,
                    data={
                        'status': 400,
                        'success': False,
                        'error': f'{ValidationError.__name__}: {state} is not a valid state',
                        'message': f"Valid states are [{', '.join(STATE_MRP)}]"
                    }
                )
            domain.append(('state', '=', state))
        
        
        production = request.env['mrp.production'].search_read(
            domain, 
            [
                'product_id',
                'request_id',
                'name',
                'product_qty',
                'qty_producing',
                'scrap_count',
                'remaining_qty',
                'efisiensi',
                'state'
            ],
            order='production_group_id desc', 
            limit=limit_val, 
            offset=offset_val
        )
        _logger.info("Production is %s", production)
        
        formatted_data =[]
        
        for prod in production:
            formatted_data.append({
                'product': prod['product_id'][1] if prod.get('product_id') else '',
                'request': prod['request_id'][1] if prod.get('request_id') else '',
                'order': prod.get('name'),
                'plan_qty': prod.get('product_qty', 0.0),
                'produced_qty': prod.get('qty_producing', 0.0),
                'scrap_qty': prod.get('scrap_count', 0.0),
                'remaining_qty': prod.get('remaining_qty', 0.0),
                'efisiensi': f"{prod.get('efisiensi', 0.0)} %",
                'state': prod.get('state') ,
            })
        return request.make_json_response(
            status=200,
            data={
                'status': 200,
                'success': True,
                'count': len(production),
                'data': formatted_data
            },
        )


    
    @http.route('/mrp_request/report/mrp_production/<start>/<end>', type='http', auth='user')
    def get_mrp_report_xls(self, start, end, **kwargs):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Mrp Request Report')

        format_start_date = datetime.strptime(start, '%Y-%m-%d').strftime('%d-%m-%Y')
        format_end_date = datetime.strptime(end, '%Y-%m-%d').strftime('%d-%m-%Y')
        
        domain = [
            ('date_start', '>=', start),
            ('date_start', '<=', end),
        ]
        
        production = request.env['mrp.production'].search(domain, order='production_group_id desc')
        products = production.mapped('product_id')
        row = 0
        
        title_header_style = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': "#FFFFFF"
        })
        
        header_style = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': "#F2FF00"
        })
        group_style = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'fg_color': "#D9D9D9"
        })
        
        group_sum_total = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': "#D9D9D9"
        })
        
        record_style = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        record_style_green = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': "#00FC32"
        })
        record_style_yellow = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': "#FFFF00"
        })
        record_style_red = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': "#FF0000"
        })
        
        sheet.set_row(0, 30)
        
        column_widths = [40, 25, 25, 25, 15, 20, 17, 20, 15, 10]

        for i, width in enumerate(column_widths):
            sheet.set_column(i, i, width)
                

        sheet.write(row, 0, XLSX_TITLE_HEADER, title_header_style)
        row += 1
        sheet.write(row, 0, f'Print Time: {fields.Datetime.context_timestamp(self, fields.Datetime.now()).strftime("%d-%m-%Y %I:%M:%S %p")} [{request.env.user.tz or "UTC"}]')
        row += 1
        sheet.write(row, 0, f'Date Start: {format_start_date}')
        row += 1
        sheet.write(row, 0, f'Date End: {format_end_date}')
        row += 2
        
        # Header
        sheet.write(row, 0, 'Product', header_style)
        sheet.write(row, 1, 'Manufacturing Request', header_style)
        sheet.write(row, 2, 'Manufacturing Order', header_style)
        sheet.write(row, 3, 'Manufacture Date', header_style)
        sheet.write(row, 4, 'Plan Quantity', header_style)
        sheet.write(row, 5, 'Produced Quantity', header_style)
        sheet.write(row, 6, 'Scarp Quantity', header_style)
        sheet.write(row, 7, 'Remaining Quantity', header_style) 
        sheet.write(row, 8, 'Efisiensi', header_style)
        sheet.write(row, 9, 'State', header_style)
        row += 1

        for product in products:
            lines = production.filtered(lambda line: line.product_id.id == product.id)
            sheet.write(row, 0, f'{product.name} [{product.default_code}]', group_style)
            sheet.write(row, 1, None, group_style)
            sheet.write(row, 2, None, group_style)
            sheet.write(row, 3, None, group_style)
            sheet.write(row, 4, sum(lines.mapped('product_qty')), group_sum_total)
            sheet.write(row, 5, sum(lines.mapped('qty_producing')), group_sum_total)
            sheet.write(row, 6, sum(lines.mapped('scrap_count')), group_sum_total)
            sheet.write(row, 7, sum(lines.mapped('remaining_qty')), group_sum_total)
            sheet.write(row, 8, None, group_style)
            sheet.write(row, 9, None, group_style)

            row += 1
            for line in lines:
                sheet.write(row, 1, line.request_id.name or '-', record_style)
                sheet.write(row, 2, line.name, record_style)
                sheet.write(row, 3, line.date_start.strftime('%d-%m-%Y'), record_style)
                sheet.write(row, 4, line.product_qty, record_style)
                sheet.write(row, 5, line.qty_producing, record_style)
                sheet.write(row, 6, line.scrap_count, record_style)
                sheet.write(row, 7, line.remaining_qty, record_style)
                if line.efisiensi >= 80.0:
                    sheet.write(row, 8, line.efisiensi, record_style_green)
                elif line.efisiensi >= 50.0 and line.efisiensi < 80.0:
                    sheet.write(row, 8, line.efisiensi, record_style_yellow)
                else:
                    sheet.write(row, 8, line.efisiensi, record_style_red)
                sheet.write(row, 9, line.state.capitalize(), record_style)
                row += 1
        # End Table
        sheet.merge_range(row, 0, row, 3, 'Total', header_style)
        sheet.write(row, 4, sum(production.mapped('product_qty')), header_style)
        sheet.write(row, 5, sum(production.mapped('qty_producing')), header_style)
        sheet.write(row, 6, sum(production.mapped('scrap_count')), header_style)
        sheet.write(row, 7, sum(production.mapped('remaining_qty')), header_style)
        sheet.write(row, 8, None, header_style)
        sheet.write(row, 9, None, header_style)
        

        workbook.close()
        output.seek(0)
                
        file_name = f"MRP_Production_Cycle_Report_{format_start_date}_to_{format_end_date}.xlsx"
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename={file_name};')
            ]
        )