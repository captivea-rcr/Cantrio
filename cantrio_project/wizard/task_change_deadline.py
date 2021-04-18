from datetime import datetime as dt
from dateutil.relativedelta import relativedelta as rd
from odoo import api, fields, models


class TaskChangeDeadline(models.TransientModel):
    _name = 'task.change.deadline'

    task_id = fields.Many2one('project.task', string='Task')
    current_deadline = fields.Date(
        'Current deadline', related='task_id.date_deadline')
    new_deadline = fields.Date('New deadline', required=True)

    @api.multi
    def change_deadline(self):
        self.task_id.date_deadline = self.new_deadline
