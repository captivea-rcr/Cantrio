
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    max_delivery = fields.Integer(default=1)
    history_sequence = fields.Integer(default=1)
    revised_order = fields.Boolean()
    picking_seq = fields.Integer(default=1)

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        if self.picking_ids:
            for picking in self.picking_ids:
                if picking.state != 'done':
                    picking.unlink()
            self.picking_seq = 1
        return res

    def action_schedule(self):
        if not self.purchase_order:
            raise UserError('Purchase Order is Required')
        view = self.env.ref('split_order.sale_order_schedule_form')
        ctx = self.env.context.copy()
        ctx['default_order_id'] = self.id
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.schedule',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,

        }

    def action_duplicate2(self):
        if self.history_sequence:
            if self.revised_order:
                order = self.copy({'name': str(self.origin) + '.' + str(
                    self.history_sequence),
                                   'history_sequence': self.history_sequence + 1,
                                   'origin': self.origin,
                                   'revised_order': True})
                rec = self.search([('name', '=', self.origin)])
                if rec:
                    rec.history_sequence += 1
            else:
                order = self.copy(
                    {'name': str(self.name) + '.' + str(self.history_sequence),
                     'history_sequence': self.history_sequence + 1,
                     'origin': self.name, 'revised_order': True})
            self.history_sequence += 1
            view = self.env.ref('sale.view_order_form')
            ctx = self.env.context.copy()
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': order.id,
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'current',
                'context': ctx,

            }


