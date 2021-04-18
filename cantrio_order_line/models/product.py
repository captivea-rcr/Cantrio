# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def show_order_lines(self):
        return True
