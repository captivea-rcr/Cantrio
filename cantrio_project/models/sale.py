from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project_id = fields.Many2one('project.project', string='Project')

    @api.multi
    def action_create_project(self):
        self.ensure_one()
        view = self.env.ref('cantrio_project.create_project_form')
        return {
            'name': "Create a project",
            'view_mode': 'form',
            'view_id': view.id,
            'view_type': 'form',
            'res_model': 'create.project.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
            },
        }
