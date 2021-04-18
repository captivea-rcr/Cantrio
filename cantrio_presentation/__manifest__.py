# -*- coding: utf-8 -*-
{
    'name': "cantrio_presentation",
    'summary': """Create presentation PDF and convert it to Quote""",
    'description': """Create presentation PDF and convert it to Quote""",
    'author': "Nandan Jani, jani435@gmail.com",
    'category': 'Sale',
    'version': '0.5.3',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
}