from odoo import fields, api, models
from odoo.tools.translate import _

import logging
_logger = logging.getLogger(__name__)


class MrpRequestOrderReport(models.Model):
    _inherit = 'mrp.production'
    
    def _compute_efisiensi(self):
        for rec in self:
            if rec.qty_producing == 0.0:
                rec.efisiensi = 0
            else:
                rec.efisiensi =  rec.qty_producing / rec.product_qty * 100

    
    request_id = fields.Many2one('mrp.request.request', string='Request', ondelete='cascade', copy=False, readonly=True, store=True)

    request_date_assign = fields.Datetime('Assign Date', related='request_id.date_assign')
    request_approver_id  = fields.Many2one('res.users', string='Approver', related='request_id.approver_id', store=True)
    request_approve_date = fields.Datetime('Approve Date', related='request_id.approve_date', store=True)
    
    remaining_qty = fields.Float(
        'Remaining Qty', 
        digits='Product Unit',
        readonly=False, 
        tracking=True,
        store=True, 
        copy=False,
        compute='_compute_remaining_qty'
        )
    efisiensi = fields.Float('Efisiensi', compute=_compute_efisiensi)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('origin') and not vals.get('request_id'):
                request = self.env['mrp.request.request'].search([('name', '=', vals.get('origin'))], limit=1)
                if request:
                    vals['request_id'] = request.id                    
        return super(MrpRequestOrderReport, self).create(vals_list)


    @api.depends('state', 'production_group_id', 'product_qty', 'qty_producing', 'scrap_count')
    def _compute_remaining_qty(self):
        records = self.search([('production_group_id', '!=', False)])
        for rec in records:
            if  rec.state == 'done' and rec.production_group_id:
                grup_production = self.env['mrp.production'].search([('production_group_id', '=', rec.production_group_id)])
                total_product_qty = [prod.product_qty for prod in grup_production]
                total_qty_producing = [prod.qty_producing for prod in grup_production]
                rec.remaining_qty = sum(total_product_qty) - sum(total_qty_producing) + rec.scrap_count
            else :
                rec.remaining_qty = 0.0

    def show_lot_id(self):
        for rec in self:
            _logger.info(list(rec.lot_producing_ids.ids))
        return True

    def action_report_mrp_production(self):
        _logger.info('action_report_mrp_production')


    def action_assign_filter_date(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Production Report'),
            'view_mode': 'form',
            'res_model': 'mrp.production.report.wizard',
            'views': [[False, 'form']],
            'target': 'new',
        }

    # TEMP FUNC
    def action_sync_historical_request_id(self):
        mo_records = self.search([('request_id', '=', False), ('origin', '!=', False)])
        for mo in mo_records:
            request = self.env['mrp.request.request'].search([('name', '=', mo.origin)], limit=1)
            if request:
                mo.request_id = request.id
                
