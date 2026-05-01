
from odoo import fields, api, models
from odoo.exceptions import AccessDenied, UserError
from odoo.tools.translate import _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    approver_ids = fields.One2many('purchase.request.approval', 'purchase_order_id', string='Approver')


    approve_state = fields.Selection(
            selection=[
                ('approver', 'Waiting Approver...'),
                ('director', 'Waiting Director...'),
                ('approved', 'Approved'),
            ], 
            string='Approve State',
            default='approver',
            readonly=True
        )

    def action_test(self):
        print(self.env)
        
        
    def button_approve_approver(self):
        self.ensure_one()
        if not self.env.user.has_group('purchase_approval.group_purchase_approver'):
            raise AccessDenied(_('You are not allowed to approve this request.'))
        for order in self:
            if order.approve_state != 'approver':
                raise UserError(_('Request already approved.'))
            order.approver_ids.create({
                'approver_id': self.env.user.id,
                'purchase_order_id': order.id,
                'approve_date': fields.Datetime.now(),
            })
            order.approve_state = 'director'

    def button_approve_director(self):
        self.ensure_one()
        if not self.env.user.has_group('purchase_approval.group_purchase_director'):  
            raise AccessDenied(_('You are not allowed to approve this request.'))
        for order in self:
            if order.approve_state != 'director':
                raise UserError(_('Request already approved.'))
            order.approver_ids.create({
                'approver_id': self.env.user.id,
                'purchase_order_id': order.id,
                'approve_date': fields.Datetime.now(),
            })
            order.approve_state = 'approved'
            order.button_approve()
            
    
    def _approval_allowed(self):
        self.ensure_one()
        res = super()._approval_allowed()

        return res or self.env.user.has_group('purchase_approval.group_purchase_director') and self.approve_state == 'approved'
    