from datetime import datetime
from odoo import http
from odoo.http import request
import xlsxwriter
import io

XLSX_TITLE_HEADER = 'Laporan Siklus Produksi'

class MrpRequest(http.Controller):
    
    @http.route('/mrp_request/report/mrp_production/<start>/<end>', type='http', auth='user')
    def get_mrp_report_xls(self, start, end, **kwargs):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Mrp Request Report')

        format_start_date = datetime.strptime(start, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y')
        format_end_date = datetime.strptime(end, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y')
        
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
        sheet.write(row, 0, f'Print Time: {datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")}')
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
                
        file_name = f"Laporan_Produksi_{format_start_date}_ke_{format_end_date}.xlsx"
        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename={file_name};')
            ]
        )