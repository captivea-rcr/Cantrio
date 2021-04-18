# -*- coding: utf-8 -*-
{
    'name': 'Split Delivery Order',
    'summary': 'Split Delivery Order',
    'version': '0.8.0',
    'category': 'Inventory',
    'author': "Paulius Pazarauskas",
    'depends': [
        'sale_stock', 'sales_report'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale.xml',
        'views/stock_partial_picking.xml',
        'views/stock_views.xml',
        'wizards/sale_order_schedule_views.xml',
        'wizards/split_wizard_views.xml',
        'wizards/stock_picking_split_views.xml',
    ],
}
