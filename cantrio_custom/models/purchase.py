# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    developer_id = fields.Many2one('res.partner', string='Developer')
    designer_id = fields.Many2one('res.partner', string='Designer')
