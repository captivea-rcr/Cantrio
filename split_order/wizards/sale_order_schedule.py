

from odoo import api, fields, models


class SaleOrderSchedule(models.TransientModel):
    _name = 'sale.order.schedule'

    order_id = fields.Many2one('sale.order', 'Order')

    @api.multi
    def no_schedule(self):
        self.order_id.action_confirm()
        for picking in self.order_id.picking_ids:
            if picking.state != 'cancel':
                picking.move_lines.write({'state': 'unscheduled'})

    @api.multi
    def schedule(self):
        self.order_id.action_confirm()
        picking = self.order_id.picking_ids[0]
        if picking:
            return picking.picking_split(scheduling=True)
