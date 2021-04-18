# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResupplyTransferLine(models.TransientModel):
    _name = "resupply.transfer.line"

    @api.onchange("product_id")
    def onchange_product_location(self):
        self.stock_njcb = 0.0
        self.stock_njcbr = 0.0
        self.stock_njt = 0.0
        self.stock_laipn = 0.0
        self.stock_seam = 0.0
        quant = self.env["stock.quant"].search([
            ("product_id", "=", self.product_id.id)])
        for q in quant:
            if q.location_id.location_id.name == "NJCB":
                self.stock_njcb = q.quantity - q.reserved_quantity
            if q.location_id.location_id.name == "NJCBR":
                self.stock_njcbr = q.quantity - q.reserved_quantity
            if q.location_id.location_id.name == "NJT":
                self.stock_njt = q.quantity - q.reserved_quantity
            if q.location_id.location_id.name == "LAIPN":
                self.stock_laipn = q.quantity - q.reserved_quantity
            if q.location_id.location_id.name == "SEAM":
                self.stock_seam = q.quantity - q.reserved_quantity

    product_id = fields.Many2one("product.product", "Product")
    quantity = fields.Float("Quantity")
    product_uom = fields.Many2one("uom.uom", "UoM")
    src_location_id = fields.Many2one("stock.location", "Source")
    dest_location_id = fields.Many2one("stock.location", "Destination")
    stock_njcb = fields.Float("Warehouse NJCB")
    stock_njcbr = fields.Float("Warehouse NJCBR")
    stock_njt = fields.Float("Warehouse NJT")
    stock_laipn = fields.Float("Warehouse LAIPN")
    stock_seam = fields.Float("Warehouse SEAM")
    transfer_njcb = fields.Float("Transfer Qty")
    transfer_njcbr = fields.Float("Transfer Qty")
    transfer_njt = fields.Float("Transfer Qty")
    transfer_laipn = fields.Float("Transfer Qty")
    transfer_seam = fields.Float("Transfer Qty")
    resupply_id = fields.Many2one("resupply.transfer", "Resupply Ref")


class ResupplyTransfer(models.TransientModel):
    _name = "resupply.transfer"

    @api.model
    def default_get(self, fields):
        res = super(ResupplyTransfer, self).default_get(fields)
        context = self.env.context
        records = self.env["warehouse.resupply"].browse(context.get("active_ids"))
        lines = []
        for r in records:
            line_vals = {
                "product_id": r.product_id.id,
                "quantity": r.quantity,
                "product_uom": r.stock_move_id.product_uom.id,
                "dest_location_id": r.stock_move_id.location_id.id,
            }
            line = self.env["resupply.transfer.line"].new(line_vals)
            line.onchange_product_location()
            line_vals = line._convert_to_write({name: line[name] for name in line._cache})
            lines.append((0, 0, line_vals))
        res.update({"line_ids": lines})
        return res

    line_ids = fields.One2many("resupply.transfer.line", "resupply_id", "Lines")

    def get_location_by_parent(self, parent):
        view_loc = self.env["stock.location"].search([("name", "=", parent)])
        src = self.env["stock.location"].search([("location_id", "=", view_loc[0].id)], limit=1)
        return src.id

    def generate_transfer(self, line, source, dest, quantity):
        move_vals = []
        source_warehouse = self.env["stock.location"].browse(source).get_warehouse()
        move_vals = [(0, 0, {
            "name": line.product_id.name,
            "product_id": line.product_id.id,
            "product_uom_qty": quantity,
            "product_uom": line.product_uom.id,
            "location_id": source,
            "location_dest_id": dest,
        })]
        picking_vals = {
            "picking_type_id": source_warehouse.int_type_id.id,
            "location_id": source,
            "location_dest_id": dest,
            "move_ids_without_package": move_vals,
        }
        picking = self.env["stock.picking"].create(picking_vals)
        picking.action_confirm()
        return picking.id

    @api.multi
    def action_generate_transfer(self):
        picking_ids = []
        grouped_lines = {}
        for line in self.line_ids:
            if line.transfer_njcb:
                source = self.get_location_by_parent("NJCB")
                picking_id = self.generate_transfer(line, source, line.dest_location_id.id, line.transfer_njcb)
                picking_ids.append(picking_id)
            if line.transfer_njcbr:
                source = self.get_location_by_parent("NJCBR")
                picking_id = self.generate_transfer(line, source, line.dest_location_id.id, line.transfer_njcbr)
                picking_ids.append(picking_id)
            if line.transfer_njt:
                source = self.get_location_by_parent("NJT")
                picking_id = self.generate_transfer(line, source, line.dest_location_id.id, line.transfer_njt)
                picking_ids.append(picking_id)
            if line.transfer_laipn:
                source = self.get_location_by_parent("LAIPN")
                picking_id = self.generate_transfer(line, source, line.dest_location_id.id, line.transfer_laipn)
                picking_ids.append(picking_id)
            if line.transfer_seam:
                source = self.get_location_by_parent("SEAM")
                picking_id = self.generate_transfer(line, source, line.dest_location_id.id, line.transfer_seam)
                picking_ids.append(picking_id)
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', picking_ids)]
        return action
