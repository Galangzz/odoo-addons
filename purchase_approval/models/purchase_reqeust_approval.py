from odoo import fields, api, models

class PruchaseRequestApproval(models.Model):
    _name = 'purchase.request.approval'
    _description = 'Purchase Request Approval'

    approver_id = fields.Many2one('res.users', string='Approver', index=True, copy=False, readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Request')
    approve_date = fields.Datetime('Approve Date', readonly=True, copy=False)
    