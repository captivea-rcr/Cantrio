# -*- coding: utf-8 -*-
from odoo import http

# class CantrioProductDescription(http.Controller):
#     @http.route('/cantrio_product_description/cantrio_product_description/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cantrio_product_description/cantrio_product_description/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cantrio_product_description.listing', {
#             'root': '/cantrio_product_description/cantrio_product_description',
#             'objects': http.request.env['cantrio_product_description.cantrio_product_description'].search([]),
#         })

#     @http.route('/cantrio_product_description/cantrio_product_description/objects/<model("cantrio_product_description.cantrio_product_description"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cantrio_product_description.object', {
#             'object': obj
#         })