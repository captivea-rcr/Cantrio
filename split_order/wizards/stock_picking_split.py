# -*- coding: utf-8 -*-

from lxml import etree
from xml.etree import ElementTree as et

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class PickingSplit(models.TransientModel):
    _name = 'picking.split'

    picking_id = fields.Many2one('stock.picking', string='Delivery')
    initial_split_done = fields.Boolean('Initial split done')
    delivery_number = fields.Integer('Number of deliveries', default=2)
    max_delivery = fields.Integer(
        'Max. deliveries', related='picking_id.sale_id.max_delivery')
    delivery_1 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 1)],
        string='Delivery 1')
    deliver_1_date = fields.Date('Delivery 1 date')
    delivery_1_note = fields.Text('Delivery 1 note')
    delivery_2 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 2)],
        string='Delivery 2')
    deliver_2_date = fields.Date('Delivery 2 date')
    delivery_2_note = fields.Text('Delivery 2 note')
    delivery_3 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 3)],
        string='Delivery 3')
    deliver_3_date = fields.Date('Delivery 3 date')
    delivery_3_note = fields.Text('Delivery 3 note')
    delivery_4 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 4)],
        string='Delivery 4')
    deliver_4_date = fields.Date('Delivery 4 date')
    delivery_4_note = fields.Text('Delivery 4 note')
    delivery_5 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 5)],
        string='Delivery 5')
    deliver_5_date = fields.Date('Delivery 5 date')
    delivery_5_note = fields.Text('Delivery 5 note')
    delivery_6 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 6)],
        string='Delivery 6')
    deliver_6_date = fields.Date('Delivery 6 date')
    delivery_6_note = fields.Text('Delivery 6 note')
    delivery_7 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 7)],
        string='Delivery 7')
    deliver_7_date = fields.Date('Delivery 7 date')
    delivery_7_note = fields.Text('Delivery 7 note')
    delivery_8 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 8)],
        string='Delivery 8')
    deliver_8_date = fields.Date('Delivery 8 date')
    delivery_8_note = fields.Text('Delivery 8 note')
    delivery_9 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 9)],
        string='Delivery 9')
    deliver_9_date = fields.Date('Delivery 9 date')
    delivery_9_note = fields.Text('Delivery 9 note')
    delivery_10 = fields.One2many(
        'picking.split.delivery.line', 'wizard_id', domain=[('nbr', '=', 10)],
        string='Delivery 10')
    deliver_10_date = fields.Date('Delivery 10 date')
    delivery_10_note = fields.Text('Delivery 10 note')



    @api.onchange(
        'delivery_1', 'delivery_2', 'delivery_3', 'delivery_4', 'delivery_5',
        'delivery_6', 'delivery_7', 'delivery_8', 'delivery_9', 'delivery_10')
    def onchange_delivery_lines(self):
        all_lines = self.delivery_1 + self.delivery_2 + self.delivery_3\
            + self.delivery_4 + self.delivery_5 + self.delivery_6\
            + self.delivery_7 + self.delivery_8 + self.delivery_9\
            + self.delivery_10
        all_products = all_lines.mapped('product_id')
        for p in all_products:
            total_to_ship = sum(self.picking_id.move_ids_without_package.filtered(
                lambda x: x.product_id == p).mapped('product_uom_qty'))
            all_prod_lines = all_lines.filtered(lambda x: x.product_id == p)
            total_delivered = sum(all_prod_lines.mapped('product_uom_qty'))
            for line in all_prod_lines:
                line.product_qty_left = total_to_ship - total_delivered

    # @api.multi
    # def put_remaining(self):
    #     delivery = self.env.context.get('delivery')
    #     if delivery == 1:
    #         for line in self.delivery_1:
    #             line.product_uom_qty += line.product_qty_left

    @api.multi
    def generate_deliveries(self):
        if self.picking_id.sale_id.delivery_count + (self.delivery_number - 1) > self.picking_id.sale_id.max_delivery:
            raise UserError(
                _('Max delivery limit reached, please request approval.'))
        else:
            ctx = self.env.context.copy()
            ctx['generate_deliveries'] = True
            ctx['split_wizard_id'] = self.id
            for x in range(0, self.delivery_number):
                for l in self.picking_id.move_ids_without_package:
                    self.env['picking.split.delivery.line'].create({
                        'wizard_id': self.id,
                        'nbr': x + 1,
                        'product_id': l.product_id.id,
                        'product_uom_qty': l.product_uom_qty / self.delivery_number,
                        'product_uom': l.product_uom.id})
            self.initial_split_done = True
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'picking.split',
                'view_mode': 'form',
                'context': ctx,
                'target': 'new',
                'res_id': self.id,
            }

    def _create_moves(self, picking, delivery_lines, date):
        for line in delivery_lines:
            move_values = {
                'name': picking.name,
                'company_id': picking.company_id.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.product_uom_qty,
                'partner_id': picking.partner_id.id or False,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'origin': picking.origin,
                'picking_type_id': picking.picking_type_id.id,
                'group_id': self.picking_id.group_id.id,
                'warehouse_id': picking.sale_id.warehouse_id.id,
                'date': fields.Datetime.now(),
                'date_expected': date,
                'picking_id': picking.id,
            }
            move = self.env['stock.move'].sudo().with_context(
                force_company=move_values.get('company_id', False)).create(
                move_values)
            move._action_confirm()
        return True

    @api.multi
    def split_delivery(self):
        original_products = {}
        split_products = {}
        for line in self.picking_id.move_ids_without_package:
            if line.product_id.id in original_products:
                original_products[line.product_id.id] += line.product_uom_qty
            else:
                original_products[line.product_id.id] = line.product_uom_qty
            if line.product_id.id in split_products:
                continue
            else:
                total_in_other_deliveries = sum(self.env[
                    'picking.split.delivery.line'].search(
                    [('wizard_id', '=', self.id),
                     ('product_id', '=', line.product_id.id)]).mapped('product_uom_qty'))
                split_products[line.product_id.id] = total_in_other_deliveries
        for product in original_products:
            for product1 in split_products:
                if product == product1:
                    if original_products[product] < split_products[product1]:
                        pname = self.env['product.product'].browse(int(product)).name
                        raise UserError(_('Total Quanitity Can Not Exceed '+ str(original_products[product])+ ' for Product '+pname))
                    else:
                        qty = original_products[product] - split_products[product1]
                        res = self.picking_id.move_ids_without_package.filtered(
                            lambda x: x.product_id.id == product)
                        if len(res)>1:
                            raise UserError('Multiple operation lines found. Contact Paul!')
                        res.product_uom_qty = qty
        self.picking_id.scheduled_date2 = str(self.deliver_1_date) +' 00:00:00'
        # self._create_moves(
        #     self.picking_id, self.delivery_1, self.deliver_1_date)
        self.picking_id.note = self.delivery_1_note
        for l in self.picking_id.move_ids_without_package:
            for n in self.delivery_1:
                if l.product_id == n.product_id:
                    l.product_uom_qty = n.product_uom_qty
        for x in range(1, self.delivery_number):
            picking_copy = self.picking_id.copy({
                'name': '/',
                'move_lines': [],
                'move_line_ids': [],
                'sale_id': self.picking_id.sale_id.id,
                'full': False
            })
            picking_copy.sale_id = self.picking_id.sale_id.id
            picking_copy.group_id = self.picking_id.group_id.id
            # if x == 0:
            #     self._create_moves(
            #         picking_copy, self.delivery_1, self.deliver_1_date)
            #     picking_copy.note = self.delivery_1_note
            if x == 1:
                self._create_moves(
                    picking_copy, self.delivery_2, self.deliver_2_date)
                picking_copy.note = self.delivery_2_note
            if x == 2:
                self._create_moves(
                    picking_copy, self.delivery_3, self.deliver_3_date)
                picking_copy.note = self.delivery_3_note
            if x == 3:
                self._create_moves(
                    picking_copy, self.delivery_4, self.deliver_4_date)
                picking_copy.note = self.delivery_4_note
            if x == 4:
                self._create_moves(
                    picking_copy, self.delivery_5, self.deliver_5_date)
                picking_copy.note = self.delivery_5_note
            if x == 5:
                self._create_moves(
                    picking_copy, self.delivery_6, self.deliver_6_date)
                picking_copy.note = self.delivery_6_note
            if x == 6:
                self._create_moves(
                    picking_copy, self.delivery_7, self.deliver_7_date)
                picking_copy.note = self.delivery_7_note
            if x == 7:
                self._create_moves(
                    picking_copy, self.delivery_8, self.deliver_8_date)
                picking_copy.note = self.delivery_8_note
            if x == 8:
                self._create_moves(
                    picking_copy, self.delivery_9, self.deliver_9_date)
                picking_copy.note = self.delivery_9_note
            if x == 9:
                self._create_moves(
                    picking_copy, self.delivery_10, self.deliver_10_date)
                picking_copy.note = self.delivery_10_note


class PickingSplitDelivery(models.TransientModel):
    _name = 'picking.split.delivery'

    wizard_id = fields.Many2one('picking.split')
    nbr = fields.Integer('Number')
    name = fields.Char('Delivery #')
    delivery_date = fields.Date('Delivery date')
    # line_ids = fields.One2many(
    #     'picking.split.delivery.line', 'delivery_id', string='Products', ondelete='cascade')


class PickingSplitDeliveryLine(models.TransientModel):
    _name = 'picking.split.delivery.line'

    # delivery_id = fields.Many2one('picking.split.delivery')
    wizard_id = fields.Many2one('picking.split')
    nbr = fields.Integer('Number')
    product_id = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(
        'Qty. to ship', digits=dp.get_precision('Product Unit of Measure'),
        required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    product_qty_left = fields.Float(
        'Qty. left', digits=dp.get_precision('Product Unit of Measure'),
        help='The quantity that is still left to be shipped.')

    @api.multi
    def ship_remaining(self):
        self.wizard_id.onchange_delivery_lines()
        self.product_uom_qty += self.product_qty_left
        # self.write({'product_uom_qty': self.product_uom_qty + self.product_qty_left})
        self.wizard_id.onchange_delivery_lines()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'picking.split',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.wizard_id.id,
        }

