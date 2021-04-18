# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.tools import pycompat, ustr


class Invoice(models.Model):
    _inherit = 'account.invoice'

    @api.depends('state', 'journal_id', 'date_invoice')
    def _get_sequence_prefix(self):
        if self.origin and self.type == 'out_invoice':
            order = self.env['sale.order'].search([('name', '=', self.origin)])
            self.sequence_number_next_prefix = order.name +'.'+str(order.invoice_count)
        else:

            if not self.env.user._is_system():
                for invoice in self:
                    invoice.sequence_number_next_prefix = False
                    invoice.sequence_number_next = ''
                return
            for invoice in self:
                journal_sequence, domain = invoice._get_seq_number_next_stuff()
                if (invoice.state == 'draft') and not self.search(domain, limit=1):
                    prefix, dummy = journal_sequence.with_context(ir_sequence_date=invoice.date_invoice,
                                                                  ir_sequence_date_range=invoice.date_invoice)._get_prefix_suffix()
                    invoice.sequence_number_next_prefix = prefix
                else:
                    invoice.sequence_number_next_prefix = False

    number = fields.Char(store=True, readonly=True, copy=False)
    sequence_number_next = fields.Char(string='Next Number', compute="_get_sequence_number_next", inverse="_set_sequence_next")
    sequence_number_next_prefix = fields.Char(string='Next Number Prefix', compute="_get_sequence_prefix")

    @api.multi
    def invoice_validate(self):
        res = super(Invoice, self).invoice_validate()
        order = self.env['sale.order'].search([('name', '=', self.origin)])
        if self.origin and self.type == 'out_invoice':
            order = self.env['sale.order'].search([('name', '=', self.origin)])
            self.number = order.name +'.'+str(order.invoice_count)
        return res

class Category(models.Model):
    _inherit = 'product.category'

    partner_id = fields.Many2one('res.partner')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def _compute_quote_count(self):
        self.quote_count = 0
        data = []
        team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
        res = self.env['sale.order'].search([('partner_id', '=', self.id), ('state', 'in', ['draft', 'sent']), ('team_id', '=', team.id)])
        for r in res:
            if r.history_sequence > 1:
                rec = self.env['sale.order'].search([('origin', '=', r.origin), ('state', 'in', ['draft', 'sent']), ('team_id', '=', team.id)],
                                                     order='create_date desc', limit=1)
                if rec:
                    data.append(rec.id)
            else:
                data.append(r.id)
        self.quote_count = len(list(set(data)))

    @api.one
    def _compute_order_count(self):
        self.order_count = 0
        data = []
        total = 0
        team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
        res = self.env['sale.order'].search([('partner_id', '=', self.id), ('state', 'in', ['sale', 'done']), ('team_id', '=', team.id)])
        for r in res:
            if r.history_sequence > 1:
                if r.origin:
                    rec = self.env['sale.order'].search(
                        [('origin', '=', r.origin), ('state', 'in', ['sale', 'done']), ('team_id', '=', team.id)] , order='create_date desc', limit=1)
                    if rec:
                        data.append(rec.id)
                        total+= rec.amount_total
                else:
                    data.append(r.id)
                    total+= r.amount_total    
            else:
                data.append(r.id)
                total+= r.amount_total
        self.order_count = len(list(set(data)))
        self.order_amount = total

    def view_quote(self):
        data = []
        team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
        res = self.env['sale.order'].search([('partner_id', '=', self.id), ('state', 'in', ['draft', 'sent']), ('team_id', '=', team.id)])
        for r in res:
            if r.history_sequence > 1:
                team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
                rec = self.env['sale.order'].search([('origin', '=', r.origin), ('state', 'in', ['draft', 'sent']), ('team_id', '=', team.id)]
                                                        , order='create_date desc', limit=1)
                if rec:
                    data.append(rec.id)
            else:
                data.append(r.id)
        data = list(set(data))
        view = self.env.ref('sale.view_quotation_tree_with_onboarding')
        return {
            'name': 'Quotations',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'views': [(view.id, 'tree')],
            'view_id': view.id,
            'domain': [('id', 'in', data)]
            
        }

    def view_order(self):
        data = []
        team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
        res = self.env['sale.order'].search([('partner_id', '=', self.id), ('state', 'in', ['sale', 'done']), ('team_id', '=', team.id)])
        for r in res:
            if r.history_sequence > 1:
                if r.origin:
                    team = self.env['crm.team'].search([('member_ids', 'in', self.env.user.id)])
                    rec = self.env['sale.order'].search([('origin', '=', r.origin), ('state', 'in', ['sale', 'done']), ('team_id', '=', team.id)]
                                                        , order='create_date desc', limit=1)
                    if rec:
                        data.append(rec.id)
                else:
                    data.append(r.id)    
            else:
                data.append(r.id)
        data = list(set(data))
        view = self.env.ref('sale.view_order_tree')
        return {
            'name': 'Orders',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'views': [(view.id, 'tree')],
            'view_id': view.id,
            'domain': [('id', 'in', data)]
            
        }


    @api.one
    @api.depends('child_ids')
    def _compute_child_count(self):
        self.count_child_ids = 0
        if self.child_ids:
            for child in self.child_ids:
                self.count_child_ids += 1
            
    quote_count = fields.Integer(compute="_compute_quote_count", default=0)
    order_count = fields.Integer(compute="_compute_order_count", default=0)
    count_child_ids = fields.Integer(compute='_compute_child_count', store=True, default=0)
    order_amount = fields.Float(compute='_compute_order_count', default=0)
    team_id = fields.Many2one('crm.team', 'Sales Team') 
    is_company = fields.Boolean(string='Is a Company', default=True,help="Check if the contact is a company, otherwise it is a person")


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _run_buy(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        cache = {}
        a = 2+2
        # determine qty to order
        PoLine = self.env['purchase.order.line']
        Move = self.env['stock.move']
        move_domain = [
            ('picking_type_id.code', '=', 'outgoing'),
            ('state', 'not in', ['done', 'cancel', 'draft']),
            ('product_id', '=', product_id.id)
        ]
        pol_domain = [
            ('state', 'in', ['draft', 'sent', 'to_approve']),
            ('product_id', '=', product_id.id)
        ]
        on_hand = product_id.virtual_available
        # First, get all active outgoing moves for the product
        outgoing_moves = Move.search(move_domain)
        # filter them out so we only have moves which still need to be reserved
        unreserved_moves = outgoing_moves.filtered(lambda x: (x.product_uom_qty - x.reserved_availability) > 0.0)
        unreserved_qty = sum(unreserved_moves.mapped('product_uom_qty')) - sum(unreserved_moves.mapped('reserved_availability'))
        # Get all RFQ's where product is being ordered
        rfq_lines = PoLine.search(pol_domain)
        rfq_qty = sum(rfq_lines.mapped('product_qty'))
        actual_available_qty = rfq_qty + on_hand - unreserved_qty
        qty_to_order = product_qty - actual_available_qty

        if actual_available_qty >= product_qty:
            return
        vendor = product_id.categ_id.partner_id
        
        if not vendor:
            vendor = self.env.ref('cantrio_custom.res_partner_dummy_vendor')
        suppliers = product_id.seller_ids\
                .filtered(lambda r: (not r.company_id or r.company_id == values['company_id']) and (not r.product_tmpl_id or r.product_tmpl_id == product_id.product_tmpl_id) and (r.name.id == vendor.id))
        if not suppliers:
            # msg = _('There is no vendor associated to the product %s. Please define a vendor for this product.') % (product_id.display_name,)
            # raise UserError(msg)   
            supplier = self.env['product.supplierinfo'].create({'name': vendor.id, 'product_tmpl_id': product_id.product_tmpl_id.id})
            partner = supplier.name
        else:
            supplier = self._make_po_select_supplier(values, suppliers)
            partner = supplier.name
        # we put `supplier_info` in values for extensibility purposes
        values['supplier'] = supplier

        # domain = self._make_po_get_domain(values, partner)
        # if domain in cache:
        #     po = cache[domain]
        # else:
        #     po = self.env['purchase.order'].sudo().search([dom for dom in domain])
        #     po = po[0] if po else False
        #     cache[domain] = po
        # if not po:
        vals = self._prepare_purchase_order(product_id, qty_to_order, product_uom, origin, values, partner)
        vals['date_order'] = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        company_id = values.get('company_id') and values['company_id'].id or self.env.user.company_id.id
        res_po = self.env['purchase.order'].search([('origin', '=', origin), ('state', '=', 'draft')], limit=1)
        if res_po and product_id.categ_id.partner_id.id == res_po.partner_id.id:
            po = res_po
        else:
            po = self.env['purchase.order'].with_context(force_company=company_id).sudo().create(vals)
        # po.date_order = fields.Datetime.now
        # cache[domain] = po
        # elif not po.origin or origin not in po.origin.split(', '):
        #     if po.origin:
        #         if origin:
        #             po.write({'origin': po.origin + ', ' + origin})
        #         else:
        #             po.write({'origin': po.origin})
        #     else:
        #         po.write({'origin': origin})

        # Create Line
        po_line = False
        for line in po.order_line:
            if line.product_id == product_id and line.product_uom == product_id.uom_po_id:
                if line._merge_in_existing_line(product_id, qty_to_order, product_uom, location_id, name, origin, values):
                    vals = self._update_purchase_order_line(product_id, qty_to_order, product_uom, values, line, partner)
                    po_line = line.write(vals)
                    break
        if not po_line:
            vals = self._prepare_purchase_order_line(product_id, qty_to_order, product_uom, values, po, partner)
            self.env['purchase.order.line'].sudo().create(vals)


class Terms(models.Model):
    _name = 'terms'

    name = fields.Char(required=True)
    data = fields.Text("Terms and Conditions", required=True)