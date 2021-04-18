# -*- coding: utf-8 -*-
{
    "name": "Order Purchase Approval",

    "summary": """
    """,

    "description": """
    """,

    "author": "Togar Hutabarat",
    "website": "https://www.upwork.com/fl/togarhutabarat",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Sales",
    "version": "0.1",

    # any module necessary for this one to work correctly
    "depends": ["base", "sale", "stock"],

    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "wizard/fetch_order_line_view.xml",
        "wizard/generate_rfq_view.xml",
        "views/order_line_warehouse_view.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
}
