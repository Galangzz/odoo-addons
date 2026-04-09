from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class MrpRequestLine(models.Model):
    _name = 'mrp.request.line'
    _description = 'MRP Request Line'
    
    request_id = fields.Many2one('mrp.request.request', store=True, string='Request', ondelete='cascade', required=True)
    
    request_name = fields.Char('Reference', related='request_id.name')
    request_date_assign = fields.Datetime('Assign Date', related='request_id.date_assign')

    request_approver_id  = fields.Many2one('res.users', string='Approver', related='request_id.approver_id', store=True)
    request_approve_date = fields.Datetime('Approve Date', related='request_id.approve_date', store=True)
    request_state = fields.Selection(related='request_id.state', store=True)
    
    product_id = fields.Many2one(
        'product.product', 
        string='Product', 
        required=True,
        domain="[('type', '=', 'consu')]",
        check_company=True,
    )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    product_uom_id = fields.Many2one('uom.uom', string='Unit', related='product_tmpl_id.uom_id', store=True)
    product_qty = fields.Float('Quantity to Order', required=True, digits='Product Unit', default=1, readonly=False, copy=True)
    production_id = fields.Many2one('mrp.production', string='Orders', ondelete='cascade', store=True, copy=False, readonly=True)
    schedule_date = fields.Datetime('Schedule Date', related='production_id.date_start', readonly=True, copy=False)
    state = fields.Selection(related='production_id.state', store=True)
    product_uom_qty = fields.Float(string='Total Quantity', compute='_compute_product_uom_qty', store=True)
    
    product_uom = fields.Many2one(
        'uom.uom', "Unit", required=True,
        compute="_compute_product_uom", store=True, readonly=False, precompute=True,
    )
    
    @api.depends('product_uom_id', 'product_qty', 'product_id.uom_id')
    def _compute_product_uom_qty(self):
        for production in self:
            if production.product_id.uom_id != production.product_uom_id:
                production.product_uom_qty = production.product_uom_id._compute_quantity(production.product_qty, production.product_id.uom_id)
            else:
                production.product_uom_qty = production.product_qty

    
    def process_single_request(self):
        _logger.info('process_single_request')
        for line in self:
            if line.request_id and line.request_id.approval_state != 'approved':
                raise UserError(_('Request is not approved.'))
            elif line.state:
                raise UserError(_('Request already on work.'))
            elif line.production_id:
                continue
            else:
                line.production_id = self.env['mrp.production'].create({
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'product_uom_id': line.product_uom_id.id,
                    'date_start': fields.Datetime.now(),
                    'origin': line.request_id.name
                })
            _logger.info("Product name is %s", line.product_id.name)
        return True
    
    
    # Trials
    def action_add_request_from_catalog_raw(self):
        mo = self.env['mrp.request.request'].browse(self.env.context.get('order_id'))
        return mo.with_context(child_field='line_ids').action_add_from_catalog()
        
    def _get_product_catalog_lines_data(self, parent_record=False, **kwargs):
        if not (parent_record and self):
            return {
                'quantity': 0,
            }
        self.product_id.ensure_one()
        return {
            **parent_record._get_product_price_and_data(self.product_id),
            'quantity': sum(
                self.mapped(
                    lambda line: line.product_uom._compute_quantity(
                        qty=line.product_qty,
                        to_unit=line.product_uom,
                    ),
                ),
            ),
            'readOnly': len(self) > 1,
            'uomDisplayName': len(self) == 1 and self.product_uom.display_name or self.product_id.uom_id.display_name,
        }
        
    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            line.product_uom = line.product_id.uom_id.id
