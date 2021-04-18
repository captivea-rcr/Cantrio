from odoo import api, fields, models


class ProjectTemplate(models.Model):
    _name = 'project.template'

    name = fields.Char('Template name', required=True)
    type_ids = fields.Many2many('project.task.type', 'project_task_type_template_rel', 'template_id', 'type_id', string='Project Stages')
    task_ids = fields.One2many(
        'project.template.task', 'template_id', string='Tasks')

    def prepare_project_vals(self):
        vals = {
            'name': self.name,
        }
        return vals


class ProjectTemplateTask(models.Model):
    _name = 'project.template.task'

    @api.multi
    @api.depends('template_id.type_ids')
    def _get_education_domain(self):
        for rec in self:
            stage_list = []
            if rec.template_id:
                stage_ids = rec.template_id.type_ids
                stage_list = [x.id for x in stage_ids]
            rec.stage_domain_ids = [(6, 0, stage_list)]

    template_id = fields.Many2one('project.template', string='Project template')
    stage_domain_ids = fields.Many2many(
        'project.task.type', compute=_get_education_domain)
    name = fields.Char('Task name', required=True)
    deadline_days = fields.Integer(
        'Deadline',
        help='The number of days entered here will be used to determine a '
             'deadline for the task (TODAY + this value)')
    stage_id = fields.Many2one('project.task.type', string='Stage')
    requires_attachment = fields.Boolean('Requires attachment')
