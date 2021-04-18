# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GenerateRFQItem(models.TransientModel):
    _name = "generate.rfq.item"

    product_id = fields.Many2one("product.product", "Product")
    quantity = fields.Float("Quantity")
    partner_id = fields.Many2one("res.partner", "Vendor")
    wizard_id = fields.Many2one("generate.rfq", "Wizard")


class GenerateRFQ(models.TransientModel):
    _name = "generate.rfq"

    @api.model
    def default_get(self, fields):
        res = super(GenerateRFQ, self).default_get(fields)
        context = self.env.context
        records = self.env["order.line.warehouse"].browse(context.get("active_ids"))
        lines = []
        for r in records:
            vendor = r.product_id.seller_ids and r.product_id.seller_ids[0].name.id or False
            line_vals = {
                "product_id": r.product_id.id,
                "quantity": r.approved_quantity,
                "partner_id": vendor,
            }
            # line = self.env["generate.rfq.item"].new(line_vals)
            # line.onchange_product_location()
            # line_vals = line._convert_to_write({name: line[name] for name in line._cache})
            lines.append((0, 0, line_vals))
        res.update({"line_ids": lines})
        return res

    line_ids = fields.One2many("generate.rfq.item", "wizard_id", "Lines")

    @api.multi
    def action_generate_rfq(self):
        rfq_ids = []
        grouped_lines = {}
        for line in self.line_ids:
            if grouped_lines.get(line.partner_id.id):
                grouped_lines[line.partner_id.id].append(line)
            else:
                grouped_lines[line.partner_id.id] = [line]
        for vendor, lines in grouped_lines.items():
            line_vals = [(0, 0, {
                "product_id": line.product_id.id,
                "name": line.product_id.name,
                "product_qty": line.quantity,
                "product_uom": line.product_id.uom_po_id.id,
                "date_planned": fields.Datetime.now(self),
                "price_unit": 0.0,
            }) for line in lines]
            rfq_vals = {
                "partner_id": vendor,
                "order_line": line_vals,
                "date_order": fields.Datetime.now(self),
                "date_planned": fields.Datetime.now(self),
            }
            rfq = self.env["purchase.order"].create(rfq_vals)
            rfq_ids.append(rfq.id)
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('id', 'in', rfq_ids)]
        return action
