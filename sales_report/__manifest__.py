# -*- coding: utf-8 -*-
{
    'name': "sales_report",

    'summary': """
        customized sales report""",

    'description': """
        customized sales report
    """,

    'author': "Nandan Jani, jani435@gmail.com",
    'website': "https://www.upwork.com/fl/nandanjani",

    'category': 'Sales',
    'version': '1.0',

    'depends': ['sale_stock', 'account'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
        
    ],
   'installable': True
}