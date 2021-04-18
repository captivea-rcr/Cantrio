from odoo import api, fields, models


class ProductSepcification(models.Model):
    _name = "product.specification"
    _description = "Product Sepcification"

    name = fields.Char("Attribute")
    sequence = fields.Integer("Sequence", default="1")
    product_categ_id = fields.Many2one("product.category", "Product Category")
    show_attribute = fields.Boolean("Show Attribute Title", default=True)
