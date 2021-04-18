# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_features = fields.Text('Product Features')
    ada = fields.Boolean('ADA')
    cupc = fields.Boolean('CUPC')
    water_sense = fields.Boolean('WaterSense')
    green_guard = fields.Boolean('GreenGuard')
    description_presentation = fields.Text('Presentation description')
    pres_category_id = fields.Many2one(
        'product.presentation.category', string='Presentation Category')


class PresentationCategory(models.Model):
    _name = 'product.presentation.category'

    name = fields.Char('Name')




