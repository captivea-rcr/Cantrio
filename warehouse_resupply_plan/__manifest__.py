# -*- coding: utf-8 -*-
{
    "name": "Warehouse Resupply Plan",

    "summary": """
    """,

    "description": """
    """,

    "author": "Togar Hutabarat",
    "website": "https://www.upwork.com/fl/togarhutabarat",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Inventory",
    "version": "0.1",

    # any module necessary for this one to work correctly
    "depends": ["base", "stock", "sale", "sale_stock", "sale_management"],

    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "wizard/fetch_resupply_data_view.xml",
        "wizard/resupply_transfer_view.xml",
        "views/warehouse_resupply_view.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
    ],
}
