# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WarehouseResupply(models.Model):
    _inherit = ["mail.thread"]
    _name = "warehouse.resupply"
    _description = "Warehouse Resupply"

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

    stock_move_id = fields.Many2one("stock.move", "Stock Move")
    product_id = fields.Many2one("product.product", "Product")
    quantity = fields.Float("Quantity")
    picking_id = fields.Many2one("Delivery Order")
    picking_number = fields.Char("Delivery Order #")
    order_line_id = fields.Many2one("sale.order.line", "Order Line", related="stock_move_id.sale_line_id")
    order_id = fields.Many2one("sale.order", "Sale Order #", related="stock_move_id.sale_line_id.order_id", store=True)
    order_warehouse_id = fields.Many2one("stock.warehouse", "Order Warehouse")
    stock_njcb = fields.Float("Warehouse NJCB", compute="get_stock_njcb")
    stock_njcbr = fields.Float("Warehouse NJCBR", compute="get_stock_njcbr")
    stock_njt = fields.Float("Warehouse NJT", compute="get_stock_njt")
    stock_laipn = fields.Float("Warehouse LAIPN", compute="get_stock_laipn")
    stock_seam = fields.Float("Warehouse SEAM", compute="get_stock_seam")
    date_expected = fields.Datetime("Expected Date", related="stock_move_id.date_expected")

    #@api.multi
    def generate_transfer(self):
        action = self.env.ref('warehouse_resupply_plan.generate_transfer_form_action').read()[0]
        return action
