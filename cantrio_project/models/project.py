from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sample_project = fields.Boolean('Sample project')
    project_stage = fields.Many2one(
        'project.task.type', string='Current stage', compute='_compute_project_stage')
    project_done = fields.Boolean('Done')
    developer_id = fields.Many2one('res.partner', string='Developer')
    designer_id = fields.Many2one('res.partner', string='Designer')

    @api.multi
    @api.depends('task_ids', 'task_ids.task_done')
    def _compute_project_stage(self):
        for rec in self:
            # Check stages in order
            stages_ordered = rec.task_ids.mapped('stage_id').sorted(key='sequence')
            for stage in stages_ordered:
                tasks_in_stage = rec.task_ids.filtered(lambda x: x.stage_id == stage)
                # Check if all tasks are complete
                stage_done = True
                for task in tasks_in_stage:
                    if not task.task_done:
                        stage_done = False
                # if at laest 1 task is not done, stay on this stage
                if not stage_done:
                    rec.project_stage = stage
                    break

    def get_current_stage_tasks(self):
        tasks = self.task_ids.filtered(lambda x: x.stage_id.id == self.project_stage.id)
        return tasks


class ProjectTask(models.Model):
    _inherit = 'project.task'

    task_done = fields.Boolean('Done')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'project_task_ir_attachments_rel', 'task_id',
        'attachment_id', string="Attachments")
    date_complete = fields.Datetime('Completion date')
    developer_id = fields.Many2one(
        'res.partner', string='Developer', related='project_id.developer_id')
    designer_id = fields.Many2one(
        'res.partner', string='Designer', related='project_id.designer_id')
    requires_attachment = fields.Boolean('Requires attachment')

    @api.multi
    @api.onchange('task_done')
    def _onchange_task_done(self):
        if self.task_done:
            now = fields.Date.today()
            return {'value': {'date_complete ': now}}
        else:
            return {'value': {'date_complete ': False}}

    @api.multi
    def action_get_attachments(self):
        return {
            'name': "Task attachments",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'task.attachment',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
                'default_attachment_ids': [(6, 0, self.attachment_ids.ids)]
            },
        }

    @api.multi
    def action_change_deadline(self):
        return {
            'name': "Change task deadline",
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'task.change.deadline',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
            },
        }

    @api.multi
    def action_task_done_toggle(self):
        if not self.task_done:
            if self.requires_attachment and len(self.attachment_ids) < 1:
                raise ValidationError(
                    _('This task requires at least 1 attachment in order to '
                      'be marked as Done.'))
            self.date_complete = fields.Datetime.now()
        else:
            self.date_complete = False
        self.task_done = not self.task_done



