

from odoo import api, fields, models


class SaleOrderSchedule(models.TransientModel):
    _name = 'sale.order.schedule'

    order_id = fields.Many2one('sale.order', 'Order')
    delivery_type = fields.Selection([('full', 'Make DO'),
                                      ('split_delivery', 'Split Delivery'),
                                      ('reserve_qty', 'Make Reservations')],
                                     stribng="Delivery Type", default='full')
    schedule_line_ids = fields.One2many("sale.order.schedule.line", "schedule_id")
    contact_name = fields.Char("Contact name")
    address = fields.Char("Address")
    phone = fields.Char("Phone")

    def done_delivery(self):
        if self.order_id.state != 'sale':
            self.order_id.action_confirm()
            picking = self.order_id.picking_ids.sorted(reverse=True)
            if picking:
                picking[0].write({'x_studio_contact_name': self.contact_name,
                                  'x_studio_contact_phone_1': self.phone})
                for move in picking[0].move_ids_without_package:
                    s_line = self.schedule_line_ids.filtered(lambda r: r.product_id == move.product_id)
                    move.product_uom_qty = s_line.do_qty
        else:
            picking = self.order_id.picking_ids.sorted(reverse=True)
            if picking:
                picking[0].write({'x_studio_contact_name': self.contact_name,
                                  'x_studio_contact_phone_1': self.phone})
                picking = picking[0].with_context({'name': str(picking[-1].name) + '-' + str(len(picking))}).copy()
                for move in picking.move_ids_without_package:
                    s_line = self.schedule_line_ids.filtered(lambda r: r.product_id == move.product_id)
                    move.product_uom_qty = s_line.do_qty

    def schedule_another(self):
        view = self.env.ref('split_order.sale_order_schedule_form')
        ctx = self.env.context.copy()
        ctx['default_order_id'] = self.order_id.id
        data = lines = self.env['sale.order.schedule.line']
        if self.order_id.state != 'sale':
            self.order_id.action_confirm()
            picking = self.order_id.picking_ids.sorted(reverse=True)
            if picking:
                picking[0].write({'x_studio_contact_name': self.contact_name,
                                  'x_studio_contact_phone_1': self.phone})
                for move in picking[0].move_ids_without_package:
                    s_line = self.schedule_line_ids.filtered(lambda r: r.product_id == move.product_id)
                    move.product_uom_qty = s_line.do_qty
            for line in self.order_id.order_line:
                minus_line = self.schedule_line_ids.filtered(lambda r: r.product_id == line.product_id)
                if line.product_uom_qty - minus_line.do_qty > 0:
                    lines |= data.create({'product_id': line.product_id.id,
                                          'product_qty': line.product_uom_qty - minus_line.do_qty})
            ctx['default_schedule_line_ids'] = [(6, 0, lines.ids)]
        else:
            picking = self.order_id.picking_ids.sorted(reverse=True)
            if picking:
                picking[0].write({'x_studio_contact_name': self.contact_name,
                                  'x_studio_contact_phone_1': self.phone})
                picking = picking[0].with_context({'name': str(picking[-1].name) + '-' + str(len(picking))}).copy()
                for move in picking.move_ids_without_package:
                    s_line = self.schedule_line_ids.filtered(lambda r: r.product_id == move.product_id)
                    move.product_uom_qty = s_line.do_qty
            for line in self.order_id.order_line:
                minus_line = self.schedule_line_ids.filtered(lambda r: r.product_id == line.product_id)
                if line.product_uom_qty - minus_line.do_qty > 0:
                    lines |= data.create({'product_id': line.product_id.id,
                                          'product_qty': minus_line.product_qty - minus_line.do_qty})
            ctx['default_schedule_line_ids'] = [(6, 0, lines.ids)]
            ctx['default_delivery_type'] = 'split_delivery'
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.schedule',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

    def make_delivery(self):
        if self.delivery_type == 'full':
            self.order_id.action_confirm()
        else:
            self.order_id.action_confirm()
            picking = self.order_id.picking_ids.sorted(reverse=True)
            if picking:
                picking[0].write({'state': 'hold'})
                for move in picking[0].move_ids_without_package:
                    s_line = self.schedule_line_ids.filtered(lambda r: r.product_id == move.product_id)
                    move.product_uom_qty = s_line.do_qty


class SaleOrderScheduleLine(models.TransientModel):
    _name = 'sale.order.schedule.line'

    product_id = fields.Many2one("product.product")
    product_qty = fields.Float("Order Quantity")
    remaining_qty = fields.Float("Remaining Order Qty", compute="_get_remaining_qty")
    do_qty = fields.Float("DO Quantity")
    onhand_qty = fields.Float("On hand Qty", related="product_id.qty_available")
    schedule_id = fields.Many2one("sale.order.schedule")

    @api.depends('do_qty', 'product_id', 'product_qty')
    def _get_remaining_qty(self):
        for rec in self:
            rec.remaining_qty = rec.product_qty - rec.do_qty