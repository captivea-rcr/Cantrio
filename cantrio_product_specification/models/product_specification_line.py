from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductSepcificationLine(models.Model):
    _name = "product.specification.line"
    _description = "Product Sepcification Line"

    name = fields.Char("Attribute")
    show_attribute = fields.Boolean("Show Attribute Title", default=True)
    sequence = fields.Integer("Sequence", default="1")
    product_id = fields.Many2one("product.template", "Product")
    value = fields.Text("Value")
