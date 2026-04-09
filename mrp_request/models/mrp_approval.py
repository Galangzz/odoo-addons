from odoo import models, fields, api

class MrpRequestApproval(models.Model):
    _name = 'mrp.request.approval'
    _description = 'MRP Request Approval'
    
    
    approver_id = fields.Many2one('res.users', string='Approver', index=True, copy=False, readonly=True)
    approve_date = fields.Datetime('Approve Date', readonly=True, copy=False)
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],  
        default='pending',
        copy=False,
        readonly=True,
        string='State',
        required=True    
    )