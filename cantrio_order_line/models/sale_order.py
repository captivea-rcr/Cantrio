# -*- coding: utf-8 -*-
from odoo import api, models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    partner_id = fields.Many2one(
        'res.partner', compute='get_sale_details', string='Customer',
        store=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product',
                                      compute='get_product_details', store=True)
    user_id = fields.Many2one(
        'res.users', string='Sales Person', compute='get_sale_details',
        store=True)
    developer_id = fields.Many2one(
        'res.partner', string='Developer', compute='get_sale_details',
        store=True)
    project_id = fields.Many2one(
        'project.project', string='Project', compute='get_sale_details',
        store=True)
    project_name = fields.Char(
        'Project', compute='get_sale_details', store=True)
    date_order = fields.Datetime(
        string='Date Order', compute='get_sale_details', store=True)
    validity_date = fields.Date(string='Validity',
                                compute='get_sale_details', store=True)

    @api.depends('order_id')
    def get_sale_details(self):
        for rec in self:
            rec.partner_id = rec.order_id.partner_id and rec.order_id.partner_id.id or False
            rec.user_id = rec.order_id.user_id and rec.order_id.user_id.id or False
            rec.project_name = rec.order_id.project_name
            rec.date_order = rec.order_id.date_order
            rec.validity_date = rec.order_id.validity_date
            rec.project_id = rec.order_id.project_id and rec.order_id.project_id.id or False
            rec.developer_id = rec.order_id.developer_id and \
                               rec.order_id.developer_id.id or False

    @api.depends('order_id', 'product_id')
    def get_product_details(self):
        for rec in self:
            rec.product_tmpl_id = rec.product_id and \
                                  rec.product_id.product_tmpl_id.id or False
