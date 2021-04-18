# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


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
                    picking.move_lines.write({'state': 'waiting', 'date_expected':  str(self.schedule_date)})


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
                'view_type': 'form',
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
