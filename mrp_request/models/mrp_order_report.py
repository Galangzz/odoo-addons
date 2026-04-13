from odoo import fields, api, models

class MrpRequestOrderReport(models.Model):
    _inherit = 'mrp.production'
    
    request_id = fields.Many2one('mrp.request.request', string='Request', ondelete='cascade', copy=False, readonly=True, store=True)

    request_date_assign = fields.Datetime('Assign Date', related='request_id.date_assign')
    request_approver_id  = fields.Many2one('res.users', string='Approver', related='request_id.approver_id', store=True)
    request_approve_date = fields.Datetime('Approve Date', related='request_id.approve_date', store=True)
    

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('origin') and not vals.get('request_id'):
                request = self.env['mrp.request.request'].search([('name', '=', vals.get('origin'))], limit=1)
                if request:
                    vals['request_id'] = request.id                    
        return super(MrpRequestOrderReport, self).create(vals_list)

    # TEMP FUNC
    def action_sync_historical_request_id(self):
        mo_records = self.search([('request_id', '=', False), ('origin', '!=', False)])
        for mo in mo_records:
            request = self.env['mrp.request.request'].search([('name', '=', mo.origin)], limit=1)
            if request:
                mo.request_id = request.id