from datetime import datetime
from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools.translate import _

class MrpProductionReportWizard(models.TransientModel):
    _name = 'mrp.production.report.wizard'
    _description = 'MRP Production Report Wizard'
    
    filter_start_date = fields.Date('Filter STart Date', default=datetime.now().strftime('%Y-%m-%d'), required=True)
    filter_end_date = fields.Date('Filter End Date', default=datetime.now().strftime('%Y-%m-%d'), required=True)
    
    format_report = fields.Selection(
        [
            ('pdf', 'PDF'),
            ('xlsx', 'XLSX')
        ], 
        string='Format Report',
        default='pdf',
        required=True,
        copy=False
    )
    
    def check_availability_report(self):
        for rec in self:
            productions = self.env['mrp.production'].search([('date_start', '>=', rec.filter_start_date), ('date_start', '<=', rec.filter_end_date)])
            if productions:
                return True
            else:
                return False
    
    def action_print_report(self):
        self.ensure_one()
        if not self.check_availability_report():
            raise UserError(_('No report available in this period'))
        for rec in self:
            if rec.format_report == 'pdf':
                return self.env.ref('mrp_request.action_report_mrp_production').report_action(self) 
            elif rec.format_report == 'xlsx':
                return {
                    'type': 'ir.actions.act_url',
                    'url': f'/mrp_request/report/mrp_production/{rec.filter_start_date}/{rec.filter_end_date}',
                    'target': 'new',
                }
