# -*- coding: utf-8 -*-
{
    'name': 'Cantrio Order Lines',
    'category': 'Sales',
    'summary': "Sale order lines view with customer, product, sale person and allow to filter and group by on it.",
    'website': 'Kalpesh Gajera <kalpesh.gajera26@gmail.com>',
    'version': '12.0.1.0',
    'author': 'Kalpesh Gajera <kalpesh.gajera26@gmail.com>',
    'depends': ['sales_report', 'cantrio_custom'],
    'demo': [
    ],
    'data': [
        'views/sale_order_line_view.xml',
        'views/res_partner_view.xml',
        'views/product_view.xml'
    ],
    'qweb': [],
    'installable': True,
    'application': True,
}
