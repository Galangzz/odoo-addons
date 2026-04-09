from odoo import fields, models, api
from odoo.tools.translate import _
import logging
from odoo.exceptions import UserError, AccessDenied
from odoo.fields import Domain, Command
from odoo.tools.misc import OrderedSet, format_date, groupby as tools_groupby, topological_sort


_logger = logging.getLogger(__name__)

PROCUREMENT_PRIORITIES = [('0', 'Normal'), ('1', 'Urgent')]

class MrpRequestRequest(models.Model):
    _name = 'mrp.request.request'
    _description = 'MRP Request'
    _inherit = ['product.catalog.mixin', 'mail.thread']
    _order = 'id desc'

    @api.model
    def _get_default_date_start(self):
        return fields.Datetime.now()


    name = fields.Char('Reference', default=lambda self: _('New'), copy=False, readonly=True)
    date_assign = fields.Datetime('Assign Date', default=_get_default_date_start, required=True, copy=False)
    priority = fields.Selection(
        PROCUREMENT_PRIORITIES, 
        string='Priority', 
        default='0',
        help="Components will be reserved first for the MO with the highest priorities.",
        copy=False
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('on_work', 'On Work'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled')
        ], 
        compute='_compute_state',
        copy=False,
        string='State',
        store=True,
        tracking=True
    )
    requested_id = fields.Many2one('res.users', string='Request By', index=True, default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    
    approval_id = fields.Many2one('mrp.request.approval', string='Approved By', index=True, readonly=True, copy=False)
    approver_id = fields.Many2one('res.users', string='Approver', related='approval_id.approver_id', readonly=True)
    approval_state = fields.Selection(string='Approval State', related='approval_id.state', readonly=True)
    approve_date = fields.Datetime(string='Approve Date', related='approval_id.approve_date', readonly=True)
    
    note = fields.Text('Note', copy=False,)
    active = fields.Boolean('Active', default=True)
    
    line_ids = fields.One2many('mrp.request.line', 'request_id', string='Order Request', copy=True, required=True)
    
    show_process_all = fields.Boolean('Show Process All', compute='_compute_show_process_all', copy=False, store=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name', False) or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('mrp.request') or _('New')
            # if vals.get('state', 'draft') == 'draft':
            #     vals['state'] = 'submitted'
        
        return super().create(vals_list)
    
    # 1. Buat field boolean penampung
    is_editable = fields.Boolean(
        string='Is Editable', 
        compute='_compute_is_editable'
    )

    @api.depends('requested_id') 
    def _compute_is_editable(self):
        for record in self:
            record.is_editable = record._allow_edits()

    @api.model
    def _allow_edits(self):
        self.ensure_one() 
        return self.env.user.has_group('mrp.group_mrp_manager') or self.requested_id == self.env.user
    
    def action_confirm(self):
        _logger.info('action_confirm_request')
        self.ensure_one()
        if not self._allow_edits():
            raise AccessDenied(_('You are not allowed to confirm this request.'))
        for request in self:
            if len(request.line_ids) == 0 or not request.line_ids:
                raise UserError(_('No product selected.'))
            elif request.state == 'draft':
                request.state = 'submitted'
            # init approval record
        approval = self.env['mrp.request.approval'].create({
            'state': 'pending'
        })
        self.approval_id = approval.id
        return True
    
    def action_approve(self):
        _logger.info('action_approve')
        if not self.env.user.has_group('mrp.group_mrp_manager'):
            raise AccessDenied(_('You are not allowed to approve this request.'))
        
        for request in self:
            if request.approval_id and request.approval_id.state == 'approved':
                raise UserError(_('Request already approved.'))
            elif request.state == 'on_work':
                raise UserError(_('Request already on work.'))
            elif request.approval_id and request.approval_id.state == 'rejected':
                request.approval_id.approver_id = self.env.user.id
                request.approval_id.approve_date = fields.Datetime.now()
                request.approval_id.state = 'approved'
            else:
                approval = self.env['mrp.request.approval'].create({
                    'approver_id': self.env.user.id,
                    'approve_date': fields.Datetime.now(),
                    'state': 'approved'
                })
                request.approval_id = approval.id
        
        return True
    
    def action_reject(self):
        
        _logger.info('action_reject')
        if not self.env.user.has_group('mrp.group_mrp_manager'):
            raise AccessDenied(_('You are not allowed to reject this request.'))

        for request in self:
            if request.approval_id and request.approval_id.state == 'rejected':
                raise UserError(_('Request already rejected.'))
            elif request.state == 'on_work':
                raise UserError(_('Request already on work.'))
            elif request.approval_id and request.approval_id.state == 'approved':
                request.approval_id.approver_id = self.env.user.id
                request.approval_id.approve_date = fields.Datetime.now()
                request.approval_id.state = 'rejected'
            else:
                approval = self.env['mrp.request.approval'].create({
                    'approver_id': self.env.user.id,
                    'approve_date': fields.Datetime.now(),
                    'state': 'rejected'
                })
                request.approval_id = approval.id
        return True
    
    def action_cancel(self):
        _logger.info('action_cancel')
        if not self.env.user.has_group('mrp.group_mrp_manager') or not self._allow_edits():
            raise AccessDenied(_('You are not allowed to cancel this request.'))
        for request in self:
            if request.state in ['draft', 'submitted']:
                request.state = 'cancelled'
        return True
    
    @api.depends('state', 'name', 'approval_id', 'approval_id.state', 'line_ids', 'line_ids.state')
    def _compute_state(self):
        for request in self:
            if not request.state or not request.approval_id or request.name == _('New'):
                request.state = 'draft'
            elif request.state == 'draft' and request.name != _('New'):
                request.state = 'submitted'
            elif request.state == 'submitted' and request.approval_id.state in ['approved', 'rejected']:
                request.state = request.approval_id.state
            elif request.state == 'approved' and request.approval_id.state == 'approved' and request.line_ids and any(line.state != 'cancel' for line in request.line_ids):
                request.state = 'on_work'
            elif request.state in ['approved', 'rejected'] and request.approval_id.state in ['approved', 'rejected']:
                request.state = request.approval_id.state
            elif request.state == 'on_work' and request.line_ids and all(line.state == 'done' for line in request.line_ids):
                request.state = 'done'
            else:
                request.state = request.state
        return True
    
    @api.constrains('line_ids')
    def _check_line_ids(self):
        for request in self:
            # if len(request.line_ids) == 0:
            #     raise UserError(_('You must add at least one product item.'))
            if request.line_ids:
                for line in request.line_ids:
                    if line.product_qty <= 0:
                        raise UserError(_('Product quantity must be greater than 0.'))
        return True
    
    def action_process_all_order(self):
        _logger.info('action_process_all_order')
        if not self.env.user.has_group('mrp.group_mrp_manager'):
            raise AccessDenied(_('You are not allowed to process all order.'))
        for request in self:
            for line in request.line_ids:
                line.process_single_request()
        return True
    
    def unlink(self):
        for request in self:
            if request.line_ids:
                for line in request.line_ids:
                    if line.production_id:
                        line.production_id.unlink()
        return super(MrpRequestRequest, self).unlink()
    
    @api.depends('line_ids', 'line_ids.state', 'state')
    def _compute_show_process_all(self):
        for request in self:
            if request.state in ['draft', 'submitted', 'rejected', 'cancelled', 'done']:
                request.show_process_all = False
            elif request.state in ['approved', 'on_work'] and any(not line.state for line in request.line_ids):
                request.show_process_all = True
            else:
                request.show_process_all = False
                

# ==============================================================
# Product Catalog
# =============================================================

    def _get_product_catalog_domain(self):
        return super()._get_product_catalog_domain() & Domain('type', '=', 'consu')

    def _default_order_line_values(self, child_field=False):
        default_data = super()._default_order_line_values(child_field)
        new_default_data = self.env['stock.move']._get_product_catalog_lines_data(parent_record=self)

        return {**default_data, **new_default_data}

    def _get_product_catalog_order_data(self, products, **kwargs):
        
        product_catalog = super()._get_product_catalog_order_data(products, **kwargs)
        for product in products:
            product_catalog[product.id] |= self._get_product_price_and_data(product)
        return product_catalog

    def _get_product_price_and_data(self, product):
        return {'price': product.standard_price}

    def _get_product_catalog_record_lines(self, product_ids, *, child_field=False, **kwargs):
        if not child_field:
            return {}
        lines = self[child_field].filtered(lambda line: line.product_id.id in product_ids)
        return lines.grouped(lambda line: line.product_id)

    def _update_order_line_info(self, product_id, quantity, *, child_field=False, **kwargs):
        if not child_field:
            return 0
        entity = self[child_field].filtered(lambda line: line.product_id.id == product_id)
        if entity:
            if quantity != 0:
                self._update_catalog_line_quantity(entity, quantity, **kwargs)
            else:
                entity.unlink()
        elif quantity > 0:
            new_line_vals = self._get_new_catalog_line_values(product_id, quantity, **kwargs)
            command = Command.create(new_line_vals)
            self.write({child_field: [command]})
            new_line = self[child_field].filtered(lambda mv: mv.product_id.id == product_id)[-1:]
            self._update_catalog_line_quantity(new_line, quantity, **kwargs)

        return self.env['product.product'].browse(product_id).standard_price

    def _update_catalog_line_quantity(self, line, quantity, **kwargs):
        line.product_uom_qty = quantity
        line.product_qty = quantity

    def _get_new_catalog_line_values(self, product_id, quantity, **kwargs):
        return {
            'product_id': product_id,
            'product_uom_qty': quantity,
        }
    
    def _is_display_stock_in_catalog(self):
        return True

    def _post_run_manufacture(self, post_production_values):
        note_subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
        for production, procurement in zip(self, post_production_values):
            if group_id := procurement.values.get('production_group_id'):
                production.production_group_id.parent_ids = [Command.link(group_id)]
            orderpoint = production.orderpoint_id
            origin_production = production.move_dest_ids.raw_material_production_id
            if orderpoint and orderpoint.create_uid.id == api.SUPERUSER_ID and orderpoint.trigger == 'manual':
                production.message_post(
                    body=_('This production order has been created from Replenishment Report.'),
                    message_type='comment',
                    subtype_id=note_subtype_id
                )
            elif orderpoint:
                production.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': production, 'origin': orderpoint},
                    subtype_id=note_subtype_id,
                )
            elif origin_production:
                production.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': production, 'origin': origin_production},
                    subtype_id=note_subtype_id,
                )
        return True

    def _resequence_workorders(self):
        self.ensure_one()

        phantom_workorders = self.workorder_ids.filtered(lambda wo: wo.operation_id.bom_id.type == 'phantom')
        for index_wo, wo in enumerate(phantom_workorders):
            wo.sequence = index_wo
        offset = len(phantom_workorders)
        non_phantom_workorders = self.workorder_ids - phantom_workorders
        for index_wo, wo in enumerate(non_phantom_workorders):
            wo.sequence = index_wo + offset
        return True

    def _track_get_fields(self):
        res = super()._track_get_fields()
        if res:
            res = OrderedSet(topological_sort(self.fields_get(res, ('depends'))))
        return res


    def _add_reference(self, reference):
        """ link the given references to the list of references. """
        self.ensure_one()
        self.reference_ids = [Command.link(stock_reference.id) for stock_reference in reference]


    def _remove_reference(self, reference):
        """ remove the given references from the list of references. """
        self.ensure_one()
        self.reference_ids = [Command.unlink(stock_reference.id) for stock_reference in reference]
