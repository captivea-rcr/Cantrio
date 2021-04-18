# -*- coding: utf-8 -*-
{
    "name": "Product Specification",

    "summary": """
        Auto-populate product description from specification templates in product category""",

    "description": """
    """,

    "author": "Togar Hutabarat",
    "website": "https://www.upwork.com/fl/togarhutabarat",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Product",
    "version": "0.1",

    # any module necessary for this one to work correctly
    "depends": ["base", "product"],

    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/product_category_view.xml",
        "views/product_view.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
}