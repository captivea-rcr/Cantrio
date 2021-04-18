from datetime import datetime as dt
from dateutil.relativedelta import relativedelta as rd
from odoo import api, fields, models


class CreateProjectWizard(models.TransientModel):
    _name = 'create.project.wizard'

    order_id = fields.Many2one('sale.order', string='Order')
    name = fields.Char('Project name')
    type = fields.Selection(
        [('prod', 'Production'), ('sample', 'Sample')], string='Type')
    project_template_id = fields.Many2one(
        'project.template', string='Project template',
        help='Base the project off of this template')

    @api.multi
    def create_project(self):
        self.ensure_one()
        vals = {
            'name': self.name,
            'sample_project': self.type == 'sample' and True or False,
            'partner_id': self.order_id.partner_id.id,
            'user_id': self.order_id.user_id.id,
        }
        if self.project_template_id:
            vals['type_ids'] = [(6, 0, self.project_template_id.type_ids.ids)]
        project = self.env['project.project'].create(vals)
        if self.project_template_id:
            for task in self.project_template_id.task_ids:
                task_vals = {
                    'name': task.name,
                    'project_id': project.id,
                    'date_deadline': (dt.today() + rd(days=task.deadline_days)).strftime('%Y-%m-%d'),
                    'stage_id': task.stage_id.id,
                    'requires_attachment': task.requires_attachment,
                }
                task_id = self.env['project.task'].create(task_vals)
        self.order_id.project_id = project
        return {'type': 'ir.actions.act_window_close'}

