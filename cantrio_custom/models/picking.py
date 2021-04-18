from odoo import api, fields, models


class Picking(models.Model):
    _inherit = 'stock.picking'

    developer_id = fields.Many2one('res.partner', string='Developer')
    designer_id = fields.Many2one('res.partner', string='Designer')
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Address', related='sale_id.partner_invoice_id')
    project_name = fields.Char(
        'Project Name', related='sale_id.project_name',
        track_visibility='onchange')
    contact_name = fields.Char('Contact Name')
    contact_phone = fields.Char('Contact Phone')
    customer_purchase_order = fields.Char(
        'Customer PO#', related='sale_id.purchase_order')


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    count_picking_done = fields.Integer(
        'Done', compute='_compute_count_picking_done')

    #@api.multi
    def _compute_count_picking_done(self):
        for rec in self:
            count = self.env['stock.picking'].search_count(
                [('state', '=', 'done'), ('picking_type_id', '=', rec.id)])
            rec.count_picking_done = count

    def get_action_picking_tree_unscheduled(self):
        return self._get_action('split_order.action_picking_tree_unscheduled')
