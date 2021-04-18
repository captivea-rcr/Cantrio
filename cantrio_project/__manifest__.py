# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Cantrio Project',
    'description': """Project customizations""",
    'version': '12.0.0.0.4.0',
    'category': 'Tools',
    'author': 'Paulius Pažarauskas',
    'depends': ['project', 'sale', 'web_one2many_kanban'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_template_views.xml',
        'views/project_views.xml',
        'views/project_menuitems.xml',
        'views/sale_views.xml',
        'wizard/create_project_views.xml',
        'wizard/task_attachment_views.xml',
        'wizard/task_change_deadline_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
