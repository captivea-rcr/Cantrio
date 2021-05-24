
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
        # if not self.purchase_order:
        #     raise UserError('Purchase Order is Required')
        if self.x_studio_order_type == 'Retail Based Order':
            self.action_confirm()
            self.picking_ids[0].write({'x_studio_customer_purchase_order': self.purchase_order})
            po = self.env['purchase.order'].create({
                'name': self.purchase_order,
                'partner_id': self.partner_id.id,
                'user_id': False,
                'company_id': self.company_id.id,
                'currency_id': self.partner_id.with_company(
                    self.company_id).property_purchase_currency_id.id or self.company_id.currency_id.id,
                'origin': self.name,
                'payment_term_id': self.partner_id.with_company(self.company_id).property_supplier_payment_term_id.id,
                'date_order': fields.Date.today(),
            })
            for line in self.order_line:
                self.env['purchase.order.line'].create({
                    'name': line.name,
                    'product_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_id.uom_po_id.id,
                    'price_unit': line.price_unit,
                    'order_id': po.id,
                })

        else:
            view = self.env.ref('split_order.sale_order_schedule_form')
            ctx = self.env.context.copy()
            ctx['default_order_id'] = self.id
            data = lines = self.env['sale.order.schedule.line']
            for line in self.order_line:
                lines |= data.create({'product_id': line.product_id.id,
                                      'product_qty': line.product_uom_qty,
                                      'order_qty': line.product_uom_qty,})
            ctx['default_schedule_line_ids'] = [(6, 0, lines.ids)]
            return {
                'type': 'ir.actions.act_window',
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
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': order.id,
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'current',
                'context': ctx,

            }


