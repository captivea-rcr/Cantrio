# -*- coding: utf-8 -*-
{
    'name': "Import Product Image",

    'summary': """
        This module is aim to map product image based on Internal Reference, and set the image as Product Image.
    """,

    'description': """
        This module is aim to map product image based on Internal Reference, and set the image as Product Image.
    """,

    'author': "Togar Hutabarat",
    'website': "https://www.upwork.com/fl/togarhutabarat",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'stock'
    ],

    # always loaded
    'data': [
        'wizard/product_image_views.xml',
    ],
}