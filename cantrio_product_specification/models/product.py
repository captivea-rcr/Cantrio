from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    specification_line_ids = fields.One2many("product.specification.line", "product_id")

    @api.onchange("categ_id")
    def onchange_category(self):
        self.specification_line_ids = [(2, sp.id) for sp in self.specification_line_ids]
        self.specification_line_ids = [(0, 0, {
            "name": sp.name,
            "show_attribute": sp.show_attribute}) for sp in self.categ_id.specification_ids]

    @api.onchange("specification_line_ids", "specification_line_ids.name", "specification_line_ids.value", "specification_line_ids.show_attribute")
    def onchange_spec(self):
        spec_list = []
        for line in self.specification_line_ids:
            if line.show_attribute:
                spec_list.append("%s: %s" % (line.name, line.value or "N/A"))
            else:
                spec_list.append("%s" % (line.value or "N/A"))
        description_sale = "\n".join(spec_list)
        self.description_sale = description_sale
