# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    developer_id = fields.Many2one('res.partner', string='Developer')
    designer_id = fields.Many2one('res.partner', string='Designer')
    terms = fields.Many2one('terms', string="Terms and Conditions")
    order_line = fields.One2many('sale.order.line', 'order_id',
                                 string='Order Lines',
                                 states={'cancel': [('readonly', True)],
                                         'done': [('readonly', True)]},
                                 copy=True, auto_join=True,
                                 track_visibility='onchange')
    tax_ids = fields.Many2many("account.tax", "order_tax_rel", "order_id", "tax_id", "Tax")

    @api.onchange("tax_ids")
    def onchange_tax(self):
        for line in self.order_line:
            line.tax_id = [(3, tax.id) for tax in line.tax_id]
            if self.tax_ids:
                line.tax_id = [(4, tax.id) for tax in self.tax_ids]

    @api.onchange('terms')
    def onchange_terms(self):
        if self.terms:
            self.note = self.terms.data

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    def get_team_domain(self):
        if self.env.user.has_group('sales_team.group_sale_manager'):
            return []
        if self.env.user.has_group('sales_team.group_sale_salesman'):
            return [('member_ids', 'in', [self.env.user.id])]

    team_id = fields.Many2one('crm.team', 'Sales Team', change_default=True,
                              default=_get_default_team, oldname='section_id',
                              domain=lambda self: self.get_team_domain())

    @api.multi
    def preview_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': self.get_portal_url(report_type='pdf'),
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    cost_ldp = fields.Float('LDP Cost', related='product_id.cost_ldp')


class SaleReport(models.Model):
    _inherit = "sale.report"

    developer_id = fields.Many2one('res.partner', string='Developer', readonly=True)
    designer_id = fields.Many2one('res.partner', string='Designer', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['developer_id'] = ', developer.id as developer_id'
        fields['designer_id'] = ', designer.id as designer_id'

        groupby += """, developer.id
        , designer.id
        """
        from_clause += """
            left join res_partner developer on s.developer_id = developer.id
            left join res_partner designer on s.designer_id = designer.id"""
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
