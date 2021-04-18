from datetime import datetime as dt
from dateutil.relativedelta import relativedelta as rd
from odoo import api, fields, models


class TaskAttachment(models.TransientModel):
    _name = 'task.attachment'

    task_id = fields.Many2one('project.task', string='Task')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    @api.multi
    def save_attachments(self):
        self.task_id.attachment_ids = self.attachment_ids