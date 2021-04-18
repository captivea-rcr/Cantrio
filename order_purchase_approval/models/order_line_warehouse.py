# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class OrderLineWarehouse(models.Model):
    _name = "order.line.warehouse"
    _description = "Order Line Warehouse"
    _inherit = ["mail.thread"]
    _rec_name = "product_id"

    @api.one
    @api.depends("product_id")
    def get_stock_njcb(self):
        self.stock_njcb = 0.0
        view_loc = self.env["stock.location"].search([("name", "=", "NJCB")])
        if view_loc:
            stock_location = self.env["stock.location"].search([
                ("location_id", "=", view_loc[0].id)])
            quant = self.env["stock.quant"].search([
                ("product_id", "=", self.product_id.id),
                ("location_id", "=", stock_location[0].id)])
            self.stock_njcb = sum([q.quantity - q.reserved_quantity for q in quant])

    @api.one
    @api.depends("product_id")
    def get_stock_njcbr(self):
        self.stock_njcbr = 0.0
        view_loc = self.env["stock.location"].search([("name", "=", "NJCBR")])
        if view_loc:
            stock_location = self.env["stock.location"].search([
                ("location_id", "=", view_loc[0].id)])
            quant = self.env["stock.quant"].search([
                ("product_id", "=", self.product_id.id),
                ("location_id", "=", stock_location[0].id)])
            self.stock_njcbr = sum([q.quantity - q.reserved_quantity for q in quant])

    @api.one
    @api.depends("product_id")
    def get_stock_njt(self):
        self.stock_njt = 0.0
        view_loc = self.env["stock.location"].search([("name", "=", "NJT")])
        if view_loc:
            stock_location = self.env["stock.location"].search([
                ("location_id", "=", view_loc[0].id)])
            quant = self.env["stock.quant"].search([
                ("product_id", "=", self.product_id.id),
                ("location_id", "=", stock_location[0].id)])
            self.stock_njt = sum([q.quantity - q.reserved_quantity for q in quant])

    @api.one
    @api.depends("product_id")
    def get_stock_laipn(self):
        self.stock_laipn = 0.0
        view_loc = self.env["stock.location"].search([("name", "=", "LAIPN")])
        if view_loc:
            stock_location = self.env["stock.location"].search([
                ("location_id", "=", view_loc[0].id)])
            quant = self.env["stock.quant"].search([
                ("product_id", "=", self.product_id.id),
                ("location_id", "=", stock_location[0].id)])
            self.stock_laipn = sum([q.quantity - q.reserved_quantity for q in quant])

    @api.one
    @api.depends("product_id")
    def get_stock_seam(self):
        self.stock_seam = 0.0
        view_loc = self.env["stock.location"].search([("name", "=", "SEAM")])
        if view_loc:
            stock_location = self.env["stock.location"].search([
                ("location_id", "=", view_loc[0].id)])
            quant = self.env["stock.quant"].search([
                ("product_id", "=", self.product_id.id),
                ("location_id", "=", stock_location[0].id)])
            self.stock_seam = sum([q.quantity - q.reserved_quantity for q in quant])

    @api.one
    @api.depends("product_id")
    def get_demand(self):
        self.remaining_demand = self.total_order_qty - (self.stock_njcb + self.stock_njcbr + self.stock_njt + self.stock_laipn + self.stock_seam + self.total_rfq + self.total_po + self.total_transit)

    @api.one
    @api.depends("product_id")
    def get_total_po(self):
        purchase_line = self.env["purchase.order.line"].search([("product_id", "=", self.product_id.id)])
        rfq = sum([line.product_qty for line in purchase_line if line.state in ["draft", "sent", "to approve"]])
        po = sum([line.product_qty for line in purchase_line if line.state in ["purchase"]])
        self.total_rfq = rfq
        self.total_po = po

    @api.one
    @api.depends("product_id")
    def get_total_transit(self):
        self.total_transit = 0.0

    product_id = fields.Many2one("product.product", "Product")
    total_order_qty = fields.Float("Total Sales Order")
    stock_njcb = fields.Float("Warehouse NJCB", compute="get_stock_njcb")
    stock_njcbr = fields.Float("Warehouse NJCBR", compute="get_stock_njcbr")
    stock_njt = fields.Float("Warehouse NJT", compute="get_stock_njt")
    stock_laipn = fields.Float("Warehouse LAIPN", compute="get_stock_laipn")
    stock_seam = fields.Float("Warehouse SEAM", compute="get_stock_seam")
    total_rfq = fields.Float("Total RFQ", compute="get_total_po")
    total_po = fields.Float("Total PO", compute="get_total_po")
    total_transit = fields.Float("Total In Transit", compute="get_total_transit")
    remaining_demand = fields.Float("Remaining Demand", compute="get_demand")
    approved_quantity = fields.Float("Approved Quantity")
    order_detail_ids = fields.One2many("order.warehouse.detail", "order_warehouse_id", "Order Details")

    @api.multi
    def do_nothing(self):
        return True

    @api.multi
    def generate_rfq(self):
        action = self.env.ref("order_purchase_approval.generate_rfq_form_action").read()[0]
        return action

    @api.multi
    def action_detail(self):
        # action = self.env.ref("order_purchase_approval.open_detail_form_action").read()[0]
        return {
            "name": _("Details"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "order.line.warehouse",
            "res_id": self.env.context.get("active_id"),
            "view_id": self.env.ref("order_purchase_approval.open_order_line_warehouse_detail_form").id,
            "target": "new",
            "type": "ir.actions.act_window",
        }
