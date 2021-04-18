# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare
from odoo.exceptions import UserError



class ScheduleWizard(models.TransientModel):
    _name = 'schedule.wizard'

    def no_schedule(self):
        order_id =  self.env.context.get('active_id', False)
        if order_id:
            order = self.env['sale.order'].browse(order_id)
            if order:
                order.action_confirm()
                for picking in order.picking_ids:
                    if picking.state != 'cancel':
                        picking.move_lines.write({'state': 'unscheduled'})

    def yes_schedule(self):
        
        view = self.env.ref('split_order.view_schedule_wizard_form')
        order_id =  self.env.context.get('active_id', False)
        if order_id:
            schedule = self.env['schedule.delivery'].create({'order_id': order_id})
            ctx = self.env.context.copy()
            product_id_list = []
            for line in self.env['sale.order'].browse(order_id).order_line:
                product_id_list.append(line.product_id.id)
            ctx['product_ids'] = product_id_list
            order = self.env['sale.order'].browse(order_id)
            for i in range(0, order.max_delivery):
                wizard_line = self.env['schedule.wizard.line'].create({'order_id': order_id, 'schedule_id': schedule.id, 'name': 'Delivery '+str(i+1)})
                for line in order.order_line:
                    self.env['schedule.delivery.line'].create({'order_id': order.id, 'wizard_line_id': wizard_line.id, 'name': 'Delivery '+str(i+1),
                        'product_id': line.product_id.id, 'product_uom_qty': line.product_uom_qty,
                         'product_uom': line.product_uom.id, 'order_line': line.id})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'schedule.delivery',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
                'res_id': schedule.id
            }


class ScheduleDelivery(models.TransientModel):
    _name = 'schedule.delivery'

    order_id = fields.Many2one('sale.order')
    schedule_lines = fields.One2many('schedule.wizard.line', 'schedule_id')
    
    def action_confirm(self):
        record = self.schedule_lines.create({'schedule_id': self.id, 'name': self.order_id.name, 'order_id': self.order_id.id,
            'delivery_date': fields.Datetime.now(), 'full': True})
        products = {}
        for line in self.order_id.order_line:
            if line.product_id.id in products:
                products[line.product_id.id] += line.product_uom_qty
            else:
                products[line.product_id.id] = line.product_uom_qty
        products1 = {}
        for lines in self.schedule_lines:
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
                       if qty > 0:
                           res = self.env['schedule.delivery.line'].search([('product_id', '=', product), ('order_id', '=', self.order_id.id)], limit=1)
                           new_line = res.copy({'product_uom_qty': qty, 'wizard_line_id': record.id, 'delivery_date': fields.Datetime.now()})
        self.order_id.picking_seq = 1
        self.order_id.action_confirm()


class ScheduleWizardLine(models.TransientModel):
    _name = 'schedule.wizard.line'

    schedule_id = fields.Many2one('schedule.delivery', ondelete='cascade')
    order_id = fields.Many2one('sale.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False, readonly=True)
    name = fields.Text(string='Description', required=True)
    delivery_date = fields.Date()
    main_lines = fields.One2many('schedule.delivery.line', 'wizard_line_id')
    full = fields.Boolean()

    def action_launch_rule_scheduled(self, sline):
        
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        # group_id = sline.order_id.procurement_group_id
        # if not group_id:
        group_id = self.env['procurement.group'].create({
            'name': sline.order_id.name, 'move_type': sline.order_id.picking_policy,
            'sale_id': sline.order_id.id,
            'partner_id': sline.order_id.partner_shipping_id.id,
        })
        for line in sline.main_lines:
            qty = line.product_uom_qty
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:

                values = {
                    'company_id': line.order_id.company_id,
                    'group_id': group_id,
                    'sale_line_id': line.order_line.id,
                    'date_planned': line.wizard_line_id.delivery_date,
                    'route_ids': line.route_id,
                    'warehouse_id': line.order_id.warehouse_id or False,
                    'partner_id': line.order_id.partner_shipping_id.id,
                }
                product_qty = line.product_uom_qty

                procurement_uom = line.product_uom
                quant_uom = line.product_id.uom_id
                get_param = self.env['ir.config_parameter'].sudo().get_param
                if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                    product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                    procurement_uom = quant_uom

                try:
                    if not line.name:
                        line.name = line.order_id.name
                    if sline.full:
                        self.env['procurement.group'].with_context(full=True).run(line.product_id, product_qty, procurement_uom, line.order_id.partner_shipping_id.property_stock_customer, line.name, line.order_id.name, values)
                    else:
                        self.env['procurement.group'].with_context(full=False).run(line.product_id, product_qty, procurement_uom, line.order_id.partner_shipping_id.property_stock_customer, line.name, line.order_id.name, values)
                except UserError as error:
                    errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        return True


class ScheduleDeliveryLine(models.TransientModel):
    _name = 'schedule.delivery.line'

    name = fields.Char(default= lambda self: self.wizard_line_id.name)
    order_id = fields.Many2one('sale.order', default=lambda self: self.env.context.get('active_id'))
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)])
    wizard_line_id = fields.Many2one('schedule.wizard.line', ondelete='cascade')
    delivery_date = fields.Date()
    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    route_id = fields.Many2one('stock.location.route', string='Route', domain=[('sale_selectable', '=', True)], ondelete='restrict')
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default='line_section', help="Technical field for UX purpose.")
    order_line = fields.Many2one('sale.order.line')

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id
            self.name = self.product_id.uom_id.name

    def refresh(self):
        
        if self.order_id:
            order_id = self.order_id.id
        else:
            order_id = int(self.env.context.get('active_id', False))
        res = self.search([('order_id', '=', order_id), ('product_id', '=', self.product_id.id), ('id', '!=', self.id)])
        for r in res:
            if r.product_id.id == self.product_id.id:
                r.product_uom_qty = r.product_uom_qty - self.product_uom_qty
        
        return {
        "type": "ir.actions.do_nothing",
    }

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_image = fields.Binary('Product Image', related="product_id.image", store=False, readonly=True)

    #@api.multi
    def _action_launch_stock_rule(self):
        if self.env.context.get('schedule_delivery', False):
            schedule_id = self.env['schedule.delivery'].browse(self.env.context.get('schedule_delivery'))
            for sline in schedule_id.schedule_lines:
                if not sline.delivery_date:
                    raise UserError('Enter delivery date for '+sline.name)
                sline.action_launch_rule_scheduled(sline)
                if sline.full:
                    for picking in schedule_id.order_id.picking_ids:
                        if picking.full:
                            picking.state= 'hold'
                            picking.move_lines.write({'state': 'hold'})
        else:
            super(SaleOrderLine, self)._action_launch_stock_rule()

