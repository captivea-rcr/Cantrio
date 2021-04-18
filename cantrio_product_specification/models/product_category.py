from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    specification_ids = fields.One2many("product.specification", "product_categ_id")
