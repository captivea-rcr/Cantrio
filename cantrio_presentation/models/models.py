# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import models, fields, api


class Presentation(models.Model):
    _name = 'presentation'
    _inherit = 'portal.mixin'

    name = fields.Char(required=True, string="Project Name")
    partner_id = fields.Many2one('res.partner', required=True, string="Customer")
    cover_image = fields.Binary(string="Cover Page Image")
    pre_date = fields.Date('Presentation Date')
    product_line = fields.One2many('product.line', 'presentation_id', string="Products")
    group_by_category = fields.Boolean("Group by Category")
    show_price = fields.Boolean('Show Price')
    show_logo = fields.Boolean('Show Poduct Logo')

    def _compute_access_url(self):
        super(Presentation, self)._compute_access_url()
        for presentation in self:
            presentation.access_url = '/my/presentation/%s' % (presentation.id)

    def get_feature_list(self, product):
        text = ''
        product = self.env['product.product'].browse(product)
        if product.product_features:
            text = product.product_features.split("\n")
        return text

    def get_category(self, product):
        category = False
        category_name = ''
        categ_id = product.categ_id
        while(not category):
            if categ_id.parent_id:
                category = False
                categ_id = categ_id.parent_id
            else:
                category = True
                category_name = categ_id.name
        return category_name

    def preview_presentation(self):
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': self.get_portal_url(report_type='pdf'),
        }

    #@api.multi
    def print_presentation(self):

        return self.env.ref('cantrio_presentation.action_report_presentation').report_action(self)

    def create_quote(self):
        so = self.env['sale.order'].create({'partner_id': self.partner_id.id, 'project_name': self.name})
        if so:
            for line in self.product_line.filtered(lambda r: r.on_quote == True):
                self.env['sale.order.line'].create({'product_id': line.product_id.id, 'order_id': so.id,
                                                    'product_uom_qty': line.product_qty, 'price_unit': line.price,})
            view = self.env.ref('sale.view_order_form')
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'current',
                'res_id': so.id
            }

    def get_sorted_products(self):
        products = self.product_line.sorted(key=lambda p: p.pres_category_id.name)
        page = 1
        prod = 0
        last_categ = self.get_category(products[0].product_id)
        current_categ = self.get_category(products[0].product_id)
        res = defaultdict(dict)
        for p in products:
            current_categ = p.pres_category_id.name
            if last_categ != current_categ:
                page += 1
                prod = 0
                last_categ = current_categ
            prod += 1
            if 'products' not in res[page]:
                res[page] = defaultdict(dict)
                res[page]['category'] = current_categ
            res[page]['products'][p.id] = {
                'product_id': p.product_id.id,
                'name': p.product_id.name,
                'image': p.product_image,
                'product_qty': p.product_qty,
                'price': p.price,
                'presentation_id': p.presentation_id,
                'description_presentation': p.product_id.description_presentation,
                'ada': p.product_id.ada,
                'cupc': p.product_id.cupc,
                'water_sense': p.product_id.water_sense,
                'green_guard': p.product_id.green_guard,
            }
            if prod == 3:
                page += 1
                prod = 0
                last_categ = current_categ
                continue
            last_categ = current_categ
        return res

    def get_unsorted_products(self):
        page = 1
        prod = 0
        res = defaultdict(dict)
        for p in self.product_line:
            prod += 1
            if 'products' not in res[page]:
                res[page] = defaultdict(dict)
            res[page]['products'][p.id] = {
                'product_id': p.product_id.id,
                'name': p.product_id.name,
                'image': p.product_image,
                'product_qty': p.product_qty,
                'price': p.price,
                'presentation_id': p.presentation_id,
                'description_presentation': p.product_id.description_presentation,
                'ada': p.product_id.ada,
                'cupc': p.product_id.cupc,
                'water_sense': p.product_id.water_sense,
                'green_guard': p.product_id.green_guard,
            }
            if prod == 3:
                page += 1
                prod = 0
        return res


class ProductLine(models.Model):
    _name = 'product.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.price = self.product_id.list_price

    sequence = fields.Integer('Sequence')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    category_id = fields.Many2one('product.category', string='Category', related='product_id.categ_id')
    product_image = fields.Binary(related='product_id.image_1920', readonly=True, string="Image")
    product_qty = fields.Integer('Quantity')
    price = fields.Float('Price')
    presentation_id = fields.Many2one('presentation')
    pres_category_id = fields.Many2one(
        'product.presentation.category', string='Presentation Category', related='product_id.pres_category_id')
    on_quote = fields.Boolean("On Quote")
    sale_order_id = fields.Many2one("sale.order", "Sale Order")
    created_from_so_line = fields.Boolean("created from so Line")

    @api.model
    def create(self, vals):
        if vals.get('on_quote') and not vals.get('created_from_so_line'):
            self.env['sale.order.line'].create({
                'order_id': vals.get('sale_order_id'),
                'product_id': vals.get('product_id'),
                'product_uom_qty': vals.get('product_qty'),
                'price_unit': vals.get('price'),
            })
        return super(ProductLine, self).create(vals)

    def write(self, vals):
        if vals.get('on_quote') and not self.created_from_so_line:
            self.env['sale.order.line'].create({
                'order_id': self.sale_order_id.id,
                'product_id': self.product_id.id,
                'product_uom_qty': self.product_qty,
                'price_unit': self.price,
            })
        # elif vals.get('on_quote') == False:
        #     sale_line = self.env['sale.order.line'].search([('order_id', '=', self.sale_order_id.id), ('product_id', '=', self.product_id.id)])
        #     sale_line.unlink()

        return super(ProductLine, self).write(vals)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    product_lines = fields.One2many('product.line', 'sale_order_id', string="Products")
    presentation_name = fields.Char(required=True, string="Presentation Name")
    cover_image = fields.Binary(string="Cover Page Image")
    pre_date = fields.Date('Presentation Date')
    group_by_category = fields.Boolean("Group by Category")
    show_price = fields.Boolean('Show Price')
    show_logo = fields.Boolean('Show Poduct Logo')

    def preview_presentation(self):
        return self.env.ref('cantrio_presentation.action_report_sale_presentation').report_action(self)

    def get_unsorted_products(self):
        page = 1
        prod = 0
        res = defaultdict(dict)
        for p in self.product_lines:
            prod += 1
            if 'products' not in res[page]:
                res[page] = defaultdict(dict)
            res[page]['products'][p.id] = {
                'product_id': p.product_id.id,
                'name': p.product_id.name,
                'image': p.product_image,
                'product_qty': p.product_qty,
                'price': p.price,
                'presentation_id': p.presentation_id,
                'description_presentation': p.product_id.description_presentation,
                'ada': p.product_id.ada,
                'cupc': p.product_id.cupc,
                'water_sense': p.product_id.water_sense,
                'green_guard': p.product_id.green_guard,
            }
            if prod == 3:
                page += 1
                prod = 0
        return res

    def get_feature_list(self, product):
        text = ''
        product = self.env['product.product'].browse(product)
        if product.product_features:
            text = product.product_features.split("\n")
        return text

    def get_category(self, product):
        category = False
        category_name = ''
        categ_id = product.categ_id
        while(not category):
            if categ_id.parent_id:
                category = False
                categ_id = categ_id.parent_id
            else:
                category = True
                category_name = categ_id.name
        return category_name

    def get_sorted_products(self):
        products = self.product_lines.sorted(key=lambda p: p.pres_category_id.name)
        page = 1
        prod = 0
        last_categ = self.get_category(products[0].product_id)
        current_categ = self.get_category(products[0].product_id)
        res = defaultdict(dict)
        for p in products:
            current_categ = p.pres_category_id.name
            if last_categ != current_categ:
                page += 1
                prod = 0
                last_categ = current_categ
            prod += 1
            if 'products' not in res[page]:
                res[page] = defaultdict(dict)
                res[page]['category'] = current_categ
            res[page]['products'][p.id] = {
                'product_id': p.product_id.id,
                'name': p.product_id.name,
                'image': p.product_image,
                'product_qty': p.product_qty,
                'price': p.price,
                'presentation_id': p.presentation_id,
                'description_presentation': p.product_id.description_presentation,
                'ada': p.product_id.ada,
                'cupc': p.product_id.cupc,
                'water_sense': p.product_id.water_sense,
                'green_guard': p.product_id.green_guard,
            }
            if prod == 3:
                page += 1
                prod = 0
                last_categ = current_categ
                continue
            last_categ = current_categ
        return res


# class SaleOrderLine(models.Model):
#     _inherit = "sale.order.line"

    # @api.model
    # def create(self, vals):
    #     res = super(SaleOrderLine, self).create(vals)
    #     lines = self.env['product.line'].search([('sale_order_id', '=', res.order_id.id),
    #                                              ('product_id', '=', res.product_id.id)])
    #     if not lines:
    #         new_line = self.env['product.line'].create({
    #             'sale_order_id': res.order_id.id,
    #             'product_id': res.product_id.id,
    #             'product_qty': res.product_uom_qty,
    #             'price': res.price_unit,
    #             'created_from_so_line': True,
    #         })
    #         old_lines = self.env['product.line'].search([('sale_order_id', '=', res.order_id.id)])
    #         for line in old_lines - new_line:
    #             line.sequence += 1
    #     return res
