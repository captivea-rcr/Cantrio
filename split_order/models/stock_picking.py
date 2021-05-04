# -*- coding: utf-8 -*-
from itertools import groupby
from operator import itemgetter

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class ScheduleWizard(models.TransientModel):
    _name = 'schedule.picking.wizard'

    schedule_date = fields.Date(string="Schedule Date")

    def yes_schedule(self):
        view = self.env.ref('split_order.view_schedule_wizard_form_stock')
        picking_id =  self.env.context.get('picking_id', False)
        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            if picking:
                for move in picking.move_ids_without_package:
                    print(str(self.schedule_date))
                    picking.move_lines.write({'state': 'waiting'})


class SplitWizard(models.TransientModel):
    _name = 'split.wizard'

    count = fields.Integer(string="How many deliveries you want to split ?")

    def yes_schedule(self):
        view = self.env.ref('split_order.view_schedule_wizard_form_stock')
        picking_id =  self.env.context.get('picking_id', False)
        self.env['schedule.wizard.line.stock'].search([('picking_id', '=', picking_id)]).unlink()
        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            ctx = self.env.context.copy()
            product_id_list = []
            for line in picking.move_ids_without_package:
                product_id_list.append(line.product_id.id)
            ctx['product_ids1'] = product_id_list
            for i in range(0, self.count):
                wizard_line = self.env['schedule.wizard.line.stock'].create({'picking_id': picking_id,  'name': 'Delivery '+str(i+1)})
                for line in picking.move_ids_without_package:
                    self.env['schedule.delivery.line.stock'].create({'picking_id': picking_id, 'wizard_line_id': wizard_line.id, 'name': 'Delivery '+str(i+1),
                        'product_id': line.product_id.id, 'product_uom_qty': line.product_uom_qty, 'product_uom': line.product_uom.id})


            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
                'res_id': picking.id
            }

class ScheduleWizardLine(models.TransientModel):
    _name = 'schedule.wizard.line.stock'

    picking_id = fields.Many2one('stock.picking', required=True, ondelete='cascade', index=True, copy=False, readonly=True)
    name = fields.Text(string='Description', required=True)
    delivery_date = fields.Date()
    main_lines = fields.One2many('schedule.delivery.line.stock', 'wizard_line_id')



class ScheduleDeliveryLine(models.TransientModel):
    _name = 'schedule.delivery.line.stock'

    name = fields.Char(default= lambda self: self.wizard_line_id.name)
    picking_id = fields.Many2one('stock.picking', default=lambda self: self.env.context.get('picking_id'))
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)])
    wizard_line_id = fields.Many2one('schedule.wizard.line.stock', ondelete='cascade')
    delivery_date = fields.Date()
    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    route_id = fields.Many2one('stock.location.route', string='Route', domain=[('sale_selectable', '=', True)], ondelete='restrict')
    max_qty = fields.Integer()

    def refresh(self):

        if self.picking_id:
            picking = self.picking_id.id
        else:
            picking = int(self.env.context.get('picking_id'))
        res = self.search([('picking_id', '=', picking), ('product_id', '=', self.product_id.id), ('id', '!=', self.id)])
        for r in res:
            if r.product_id.id == self.product_id.id:
                r.product_uom_qty = r.product_uom_qty - self.product_uom_qty

        return {
        "type": "ir.actions.do_nothing",
    }

class StockMove(models.Model):
    _inherit = 'stock.move'

    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done'),
        ('hold', 'On Hold'),
        ('unscheduled', 'Unscheduled'),
        ], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the stock move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'. \n"
             " * On Hold: waiting for delivery instructions.")

    def _action_assign(self):
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `product_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """
        assigned_moves = self.env['stock.move']
        partially_available_moves = self.env['stock.move']
        # Read the `reserved_availability` field of the moves out of the loop to prevent unwanted
        # cache invalidation when actually reserving the move.
        reserved_availability = {move: move.reserved_availability for move in self}
        roundings = {move: move.product_id.uom_id.rounding for move in self}
        for move in self:
            if move.procure_method == 'make_to_order':
                move.procure_method = 'make_to_stock'
        for move in self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available', 'unscheduled']):
            rounding = roundings[move]
            missing_reserved_uom_quantity = move.product_uom_qty - reserved_availability[move]
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity, move.product_id.uom_id, rounding_method='HALF-UP')
            if move.location_id.should_bypass_reservation()\
                    or move.product_id.type == 'consu':
                # create the move line(s) but do not impact quants
                if move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    for i in range(0, int(missing_reserved_quantity)):
                        self.env['stock.move.line'].create(move._prepare_move_line_vals(quantity=1))
                else:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                            ml.location_id == move.location_id and
                                                            ml.location_dest_id == move.location_dest_id and
                                                            ml.picking_id == move.picking_id and
                                                            not ml.lot_id and
                                                            not ml.package_id and
                                                            not ml.owner_id)
                    if to_update:
                        to_update[0].product_uom_qty += missing_reserved_uom_quantity
                    else:
                        self.env['stock.move.line'].create(move._prepare_move_line_vals(quantity=missing_reserved_quantity))
                assigned_moves |= move
            else:
                if not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    # If we don't need any quantity, consider the move assigned.
                    need = missing_reserved_quantity
                    if float_is_zero(need, precision_rounding=rounding):
                        assigned_moves |= move
                        continue
                    # Reserve new quants and create move lines accordingly.
                    forced_package_id = move.package_level_id.package_id or None
                    available_quantity = self.env['stock.quant']._get_available_quantity(move.product_id, move.location_id, package_id=forced_package_id)
                    if available_quantity <= 0:
                        continue
                    taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id, package_id=forced_package_id, strict=False)
                    if float_is_zero(taken_quantity, precision_rounding=rounding):
                        continue
                    if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
                        assigned_moves |= move
                    else:
                        partially_available_moves |= move
                else:
                    # Check what our parents brought and what our siblings took in order to
                    # determine what we can distribute.
                    # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                    # the reserved quantity on the quants, convert it here in
                    # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                    move_lines_in = move.move_orig_ids.filtered(lambda m: m.state == 'done').mapped('move_line_ids')
                    keys_in_groupby = ['location_dest_id', 'lot_id', 'result_package_id', 'owner_id']

                    def _keys_in_sorted(ml):
                        return (ml.location_dest_id.id, ml.lot_id.id, ml.result_package_id.id, ml.owner_id.id)

                    grouped_move_lines_in = {}
                    for k, g in groupby(sorted(move_lines_in, key=_keys_in_sorted), key=itemgetter(*keys_in_groupby)):
                        qty_done = 0
                        for ml in g:
                            qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_in[k] = qty_done
                    move_lines_out_done = (move.move_orig_ids.mapped('move_dest_ids') - move)\
                        .filtered(lambda m: m.state in ['done'])\
                        .mapped('move_line_ids')
                    # As we defer the write on the stock.move's state at the end of the loop, there
                    # could be moves to consider in what our siblings already took.
                    moves_out_siblings = move.move_orig_ids.mapped('move_dest_ids') - move
                    moves_out_siblings_to_consider = moves_out_siblings & (assigned_moves + partially_available_moves)
                    reserved_moves_out_siblings = moves_out_siblings.filtered(lambda m: m.state in ['partially_available', 'assigned'])
                    move_lines_out_reserved = (reserved_moves_out_siblings | moves_out_siblings_to_consider).mapped('move_line_ids')
                    keys_out_groupby = ['location_id', 'lot_id', 'package_id', 'owner_id']

                    def _keys_out_sorted(ml):
                        return (ml.location_id.id, ml.lot_id.id, ml.package_id.id, ml.owner_id.id)

                    grouped_move_lines_out = {}
                    for k, g in groupby(sorted(move_lines_out_done, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                        qty_done = 0
                        for ml in g:
                            qty_done += ml.product_uom_id._compute_quantity(ml.qty_done, ml.product_id.uom_id)
                        grouped_move_lines_out[k] = qty_done
                    for k, g in groupby(sorted(move_lines_out_reserved, key=_keys_out_sorted), key=itemgetter(*keys_out_groupby)):
                        grouped_move_lines_out[k] = sum(self.env['stock.move.line'].concat(*list(g)).mapped('product_qty'))
                    available_move_lines = {key: grouped_move_lines_in[key] - grouped_move_lines_out.get(key, 0) for key in grouped_move_lines_in.keys()}
                    # pop key if the quantity available amount to 0
                    available_move_lines = dict((k, v) for k, v in available_move_lines.items() if v)

                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(lambda m: m.product_qty):
                        if available_move_lines.get((move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)):
                            available_move_lines[(move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)] -= move_line.product_qty
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        need = move.product_qty - sum(move.move_line_ids.mapped('product_qty'))
                        # `quantity` is what is brought by chained done move lines. We double check
                        # here this quantity is available on the quants themselves. If not, this
                        # could be the result of an inventory adjustment that removed totally of
                        # partially `quantity`. When this happens, we chose to reserve the maximum
                        # still available. This situation could not happen on MTS move, because in
                        # this case `quantity` is directly the quantity on the quants themselves.
                        available_quantity = self.env['stock.quant']._get_available_quantity(
                            move.product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
                        if float_is_zero(available_quantity, precision_rounding=rounding):
                            continue
                        taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity), location_id, lot_id, package_id, owner_id)
                        if float_is_zero(taken_quantity, precision_rounding=rounding):
                            continue
                        if float_is_zero(need - taken_quantity, precision_rounding=rounding):
                            assigned_moves |= move
                            break
                        partially_available_moves |= move
        partially_available_moves.write({'state': 'partially_available'})
        assigned_moves.write({'state': 'assigned'})
        self.mapped('picking_id')._check_entire_pack()

    def _action_confirm(self, merge=True, merge_into=False):

        move_create_proc = self.env['stock.move']
        move_to_confirm = self.env['stock.move']
        move_waiting = self.env['stock.move']

        to_assign = {}
        for move in self:
            # if the move is preceeded, then it's waiting (if preceeding move is done, then action_assign has been called already and its state is already available)
            if move.move_orig_ids:
                move_waiting |= move
            else:
                if move.procure_method == 'make_to_order':
                    product_id = move.product_id
                    # determine qty to order
                    PoLine = self.env['purchase.order.line']
                    Move = self.env['stock.move']
                    move_domain = [
                        ('picking_type_id.code', '=', 'outgoing'),
                        ('state', 'not in', ['done', 'cancel', 'draft']),
                        ('product_id', '=', product_id.id)
                    ]
                    pol_domain = [
                        ('state', 'in', ['draft', 'sent', 'to_approve']),
                        ('product_id', '=', product_id.id)
                    ]
                    on_hand = product_id.virtual_available
                    # First, get all active outgoing moves for the product
                    outgoing_moves = Move.search(move_domain)
                    # filter them out so we only have moves which still need to be reserved
                    unreserved_moves = outgoing_moves.filtered(
                        lambda x: (x.product_uom_qty - x.reserved_availability) > 0.0)
                    unreserved_qty = sum(
                        unreserved_moves.mapped('product_uom_qty')) - sum(
                        unreserved_moves.mapped('reserved_availability'))
                    # Get all RFQ's where product is being ordered
                    rfq_lines = PoLine.search(pol_domain)
                    rfq_qty = sum(rfq_lines.mapped('product_qty'))
                    actual_available_qty = rfq_qty + on_hand - unreserved_qty
                    if actual_available_qty > move.product_uom_qty:
                        move.procure_method = 'make_to_stock'
                        move_to_confirm |= move
                    else:
                        move_create_proc |= move
                else:
                    move_to_confirm |= move
            if move._should_be_assigned():
                key = (move.group_id.id, move.location_id.id, move.location_dest_id.id)
                if key not in to_assign:
                    to_assign[key] = self.env['stock.move']
                to_assign[key] |= move

        # create procurements for make to order moves
        for move in move_create_proc:
            values = move._prepare_procurement_values()
            origin = (move.group_id and move.group_id.name or (move.origin or move.picking_id.name or "/"))
            self.env['procurement.group'].run(move.product_id, move.product_uom_qty, move.product_uom, move.location_id, move.rule_id and move.rule_id.name or "/", origin,
                                              values)

        move_to_confirm.write({'state': 'confirmed'})
        (move_waiting | move_create_proc).write({'state': 'waiting'})

        # assign picking in batch for all confirmed move that share the same details
        for moves in to_assign.values():
            moves._assign_picking()
        self._push_apply()
        if merge:
            return self._merge_moves(merge_into=merge_into)
        return self


class StockPicking(models.Model):

    _inherit = "stock.picking"

    approved = fields.Boolean()
    schedule_lines = fields.One2many('schedule.wizard.line.stock', 'picking_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('unscheduled', 'Unscheduled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('hold', 'On Hold'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore. \n"
             " * On Hold: waiting for delivery instructions.") 
    scheduled_date2 = fields.Datetime(
        'Scheduled Date', compute='_compute_scheduled_date2', store=True,
        index=True, track_visibility='onchange',
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")
    full = fields.Boolean(default=False)
    origin = fields.Char(
        'Order', index=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Reference of the document")
    count = fields.Integer(default=0)
    # name = fields.Char( store=True, copy=False,  index=True,)

    @api.depends('move_type', 'immediate_transfer', 'move_lines.state', 'move_lines.picking_id')
    def _compute_state(self):
        ''' State of a picking depends on the state of its related stock.move
        - Draft: only used for "planned pickings"
        - Waiting: if the picking is not ready to be sent so if
          - (a) no quantity could be reserved at all or if
          - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
        - Waiting another move: if the picking is waiting for another move
        - Ready: if the picking is ready to be sent so if:
          - (a) all quantities are reserved or if
          - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
        - Done: if the picking is done.
        - Cancelled: if the picking is cancelled
        '''
        for picking in self:
            if not picking.move_lines:
                picking.state = 'draft'
            elif any(move.state == 'draft' for move in picking.move_lines):  # TDE FIXME: should be all ?
                picking.state = 'draft'
            elif all(move.state == 'cancel' for move in picking.move_lines):
                picking.state = 'cancel'
            elif all(move.state in ['cancel', 'done'] for move in picking.move_lines):
                picking.state = 'done'
            elif any(move.state == 'hold' for move in picking.move_lines):
                picking.state = 'hold'
                for move in picking.move_ids_without_package:
                    move.state = 'hold'
            else:
                relevant_move_state = picking.move_lines._get_relevant_state_among_moves()
                if picking.immediate_transfer and relevant_move_state not in ('draft', 'cancel', 'done'):
                    picking.state = 'assigned'
                elif relevant_move_state == 'partially_available':
                    picking.state = 'assigned'
                else:
                    picking.state = relevant_move_state

            if self._context.get("picking_state"):
                picking.state = self._context.get("picking_state")

    name_set = fields.Boolean()

    # _sql_constraints = [
    #     ('name_uniq', 'unique(company_id)', 'Reference must be unique per company!'),
    # ]

    #@api.multi
    def _compute_show_check_availability(self):
        for picking in self:
            has_moves_to_reserve = any(
                move.state in ('waiting', 'confirmed', 'partially_available', 'unscheduled') and
                float_compare(move.product_uom_qty, 0, precision_rounding=move.product_uom.rounding)
                for move in picking.move_lines
            )
            picking.show_check_availability = picking.is_locked and picking.state in ('confirmed', 'waiting', 'assigned', 'unscheduled') and has_moves_to_reserve


    @api.depends('full')
    def _compute_scheduled_date2(self):
        if not self.full and self.move_lines:
            self.scheduled_date2 = min(self.move_lines.mapped('date'))

    #@api.multi
    def remove_hold(self):
        self.state = 'confirmed'
        self.move_lines.write({'state': 'confirmed'})

    @api.model
    def create(self, vals):
        if self.env.context.get('full', False):
            vals['state'] = 'hold'
            vals['full'] = True
        if vals.get('origin', False):
            so = self.env['sale.order'].search([('name', '=', vals.get('origin'))])
            if so.max_delivery == 1 or so.max_delivery == 0:
                if self._context.get('name'):
                    vals['name'] = self._context.get('name')
                else:
                    vals['name'] = vals.get('origin')
            else:
                vals['name'] = vals.get('origin')+"."+str(so.picking_seq)
                so.picking_seq+=1
            # if res:
            #     print("RES+1########################################################.",res.count+1)
            #     vals['name'] = vals.get('origin')+'.'+str(res.count+1)
            #     vals['count'] = res.count+1
            # else:
            #     vals['name'] = vals.get('origin', False)
            #     vals['count'] = 1
        return super(StockPicking, self).create(vals)

    #@api.multi
    def schedule_picking(self):
        # """Use to trigger the wizard from button with correct context"""
        
        
        view = self.env.ref('split_order.schedule_picking_wizard')
        ctx = self.env.context.copy()
        ctx['picking_id'] = self.id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'schedule.picking.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
            
        }

    #@api.multi
    def split_picking(self):
        # """Use to trigger the wizard from button with correct context"""
        
        if self.sale_id.delivery_count >= self.sale_id.max_delivery:
            raise UserError(_('Max delivery limit reached, please request approval.'))
        else:
            view = self.env.ref('split_order.view_confirm_wizard_form_stock')
            ctx = self.env.context.copy()
            ctx['picking_id'] = self.id
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'split.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
                
            }

    #@api.multi
    def picking_split(self, scheduling=False):
        if self.sale_id.delivery_count >= self.sale_id.max_delivery:
            raise UserError(
                _('Max delivery limit reached, please request approval.'))
        else:
            view = self.env.ref('split_order.picking_split_form_view')
            ctx = self.env.context.copy()
            ctx['default_picking_id'] = self.id
            ctx['default_delivery_number'] = scheduling and 1 or 2
            ctx['scheduling'] = scheduling
            return {
                'name': 'Split Delivery',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'picking.split',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,

            }

    def split_process(self):
        products = {}
        record = self.schedule_lines.create({'name': self.name, 'picking_id': self.id})
        for line in self.move_ids_without_package:
            if line.product_id.id in products:
                products[line.product_id.id] += line.product_uom_qty
            else:
                products[line.product_id.id] = line.product_uom_qty
        products1 = {}
        for lines in self.schedule_lines:
            if not lines.delivery_date and lines.name != self.name:
                raise UserError('Enter delivery date for '+lines.name)
            for line in lines.main_lines:
                if line.product_id.id in products1:
                    products1[line.product_id.id] += line.product_uom_qty
                else:
                    products1[line.product_id.id] = line.product_uom_qty
        for product in products:
            for product1 in products1:
                if product == product1:
                    if products[product] < products1[product1]:
                        pname = self.env['product.product'].browse(int(product)).name
                        raise UserError(_('Total Quanitity Can Not Exceed '+ str(products[product])+ ' for Product '+pname))
                    else:
                        qty =  products[product] - products1[product1]
                        res = self.move_ids_without_package.search([('product_id', '=', product), ('picking_id', '=', self.id)])
                        for r in res:
                            r.product_uom_qty = qty

        for lines in self.schedule_lines:
            backorder_picking = lines.picking_id.copy({
                    'name': '/',
                    'move_lines': [],
                    'move_line_ids': [],
                    'sale_id': lines.picking_id.sale_id.id,
                    'full': False
                })
            
            for line in lines.main_lines:
                move_values = {
                    'name': backorder_picking.name,
                    'company_id': backorder_picking.company_id.id,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'product_uom_qty': line.product_uom_qty,
                    'partner_id': backorder_picking.partner_id.id or False,
                    'location_id': backorder_picking.location_id.id,
                    'location_dest_id': backorder_picking.location_dest_id.id,
                    # 'move_dest_ids': values.get('move_dest_ids', False) and [(4, x.id) for x in values['move_dest_ids']] or [],
                    # 'rule_id': self.id,
                    # 'procure_method': self.procure_method,
                    'origin': backorder_picking.origin,
                    'picking_type_id': self.picking_type_id.id,
                    'group_id': line.picking_id.group_id.id,
                    # 'route_ids': [(4, route.id) for route in values.get('route_ids', [])],
                    'warehouse_id': backorder_picking.sale_id.warehouse_id.id,
                    'date': fields.Datetime.now(),
                    'date': line.wizard_line_id.delivery_date,
                    # 'propagate': self.propagate,
                    # 'priority': values.get('priority', "1"),
                    'picking_id': backorder_picking.id,
                }

                move = self.env['stock.move'].sudo().with_context(force_company=move_values.get('company_id', False)).create(move_values)
               
                move._action_confirm()
                # lines.picking_id.state = 'cancel'
        res = self.move_ids_without_package.search([('product_id', '=', product), ('picking_id', '=', self.id)])
        flag = False
        for r in res:
            if r.product_uom_qty == 0:
                flag = True
            if r.product_uom_qty < 0:
                flag = False
        if flag:
            self.action_cancel()
            self.sale_id.action_view_delivery()
            # self.unlink()

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    def _compute_picking_unscheduled(self):
        res = self.env['stock.picking'].search_count([('state', 'in', ('unscheduled', 'hold')),
                 ('picking_type_id', 'in', self.ids)])

        self.count_picking_unscheduled =  res or 0
    
    count_picking_unscheduled = fields.Integer(compute='_compute_picking_unscheduled')

    def get_action_picking_tree_unscheduled(self):
        return self._get_action('split_order.action_picking_tree_unscheduled')
