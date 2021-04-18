# -*- coding: utf-8 -*-
{
    'name': "Cantrio Custom",
    'summary': """Various Cantrio specific customizations""",
    'author': "Paulius Pažarauskas",
    'category': 'Custom',
    'version': '0.14.0',
    'depends': ['sale', 'sales_report', 'purchase_stock', 'split_order', 'contacts'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/purchase_views.xml',
        'views/stock_views.xml',
        'views/sale_views.xml',
        'views/views.xml',
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}