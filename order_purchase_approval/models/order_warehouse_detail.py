# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class OrderWarehouseDetail(models.Model):
    _name = "order.warehouse.detail"
    _description = "Order Warehouse Detail"

    order_warehouse_id = fields.Many2one("order.line.warehouse", "Order Warehouse")
    partner_id = fields.Many2one("res.partner", "Customer")
    order_id = fields.Many2one("sale.order", "Sale Order")
    project_name = fields.Char("Project Name")
    order_quantity = fields.Float("Order Quantity")
    expected_date = fields.Datetime("Expected Date")
