# -*- coding: utf-8 -*-
from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #@api.multi
    def show_order_lines(self):
        return True
