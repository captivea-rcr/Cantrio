from odoo import api, fields, models


class Product(models.Model):
    _inherit = 'product.template'

    _sql_constraints = [(
        'name_uniq', 'unique (name)', 'Product with that name already exists!')]
    type_custom = fields.Selection(
        [('service', 'Service'), ('product', 'Storable product')],
        string='Product Type', default='product', compute="_get_type_custom", inverse="_set_type_custom")
    cost_freight_duties = fields.Float('Freight and Duties')
    cost_tariff = fields.Float('Tariff')
    cost_ldp = fields.Float('LDP Cost', compute='_compute_cost_ldp')

    #@api.multi
    @api.depends('cost_freight_duties', 'cost_tariff', 'standard_price')
    def _compute_cost_ldp(self):
        for rec in self:
            if rec.standard_price:
                ldp_cost = rec.standard_price
                if rec.cost_freight_duties != 0.0:
                    ldp_cost += rec.standard_price * (rec.cost_freight_duties/100)
                if rec.cost_tariff != 0.0:
                    ldp_cost += rec.standard_price * (rec.cost_tariff/100)
                rec.cost_ldp = ldp_cost

    #@api.multi
    @api.depends('type')
    def _get_type_custom(self):
        for rec in self:
            if not rec.type == 'consu':
                rec.type_custom = rec.type

    #@api.multi
    def _set_type_custom(self):
        for rec in self:
            rec.type = rec.type_custom

    @api.one
    def _compute_quote_count(self):
        self.quote_count = 0
        data = []
        total_qty = 0
        variants = self.env['product.product'].sudo().search(
            [('product_tmpl_id', '=', self.id)]).ids
        lines = self.env['sale.order.line'].sudo().search(
            [('product_id', 'in', variants),
             ('state', 'in', ['draft', 'sent'])])
        for line in lines:
            total_qty += line.product_uom_qty
        res = [l.order_id for l in lines]
        for r in res:
            if r.history_sequence > 1:
                rec = self.env['sale.order'].sudo().search(
                    [('id', '=', r.id), ('state', 'in', ['draft', 'sent'])],
                    order='create_date desc', limit=1)
                if rec:
                    data.append(rec.id)
            else:
                data.append(r.id)
        self.quote_count = len(list(set(data)))
        self.quotation_count = total_qty

    def view_quote(self):
        data = []
        variants = self.env['product.product'].sudo().search(
            [('product_tmpl_id', '=', self.id)]).ids
        lines = self.env['sale.order.line'].sudo().search(
            [('product_id', 'in', variants),
             ('state', 'in', ['draft', 'sent'])])
        res = [l.order_id for l in lines]
        for r in res:
            if r.history_sequence > 1:
                rec = self.env['sale.order'].sudo().search(
                    [('id', '=', r.id), ('state', 'in', ['draft', 'sent'])]
                    , order='create_date desc', limit=1)
                if rec:
                    data.append(rec.id)
            else:
                data.append(r.id)
        data = list(set(data))
        # view = self.env.ref('sale.view_quotation_tree')
        return {
            'name': 'Quotations',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            # 'views': [(view.id, 'tree')],
            # 'view_id': view.id,
            'domain': [('id', 'in', data)]

        }

    @api.one
    def _compute_order_count(self):
        self.order_count = 0
        data = []
        variants = self.env['product.product'].sudo().search(
            [('product_tmpl_id', '=', self.id)]).ids
        lines = self.env['sale.order.line'].sudo().search(
            [('product_id', 'in', variants), ('state', 'in', ['sale', 'done'])])
        res = [l.order_id for l in lines]
        for r in res:
            if r.history_sequence > 1:
                if r.origin:
                    rec = self.env['sale.order'].sudo().search(
                        [('origin', '=', r.origin),
                         ('state', 'in', ['sale', 'done'])]
                        , order='create_date desc', limit=1)
                    if rec:
                        data.append(rec.id)
                else:
                    data.append(r.id)
            else:
                data.append(r.id)
        self.order_count = len(list(set(data)))

    def view_order(self):
        data = []
        variants = self.env['product.product'].sudo().search(
            [('product_tmpl_id', '=', self.id)]).ids
        lines = self.env['sale.order.line'].sudo().search(
            [('product_id', 'in', variants), ('state', 'in', ['sale', 'done'])])
        res = [l.order_id for l in lines]
        for r in res:
            if r.history_sequence > 1:
                if r.origin:
                    rec = self.env['sale.order'].sudo().search(
                        [('origin', '=', r.origin),
                         ('state', 'in', ['sale', 'done'])]
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

    def _get_default_routes(self):

        res = self.env['stock.location.route'].search(
            [('name', 'in', ['Make To Order', 'Buy'])])
        ids = []
        for r in res:
            ids.append(r.id)
        return ids

    route_ids = fields.Many2many(
        'stock.location.route', 'stock_route_product', 'product_id', 'route_id',
        'Routes',
        domain=[('product_selectable', '=', True)],
        default=lambda self: self._get_default_routes(),
        help="Depending on the modules installed, this will allow you to define the route of the product: whether it will be bought, manufactured, MTO, etc.")

    order_count = fields.Integer(compute="_compute_order_count", default=0)
    quote_count = fields.Integer(compute="_compute_quote_count", default=0)
    quotation_count = fields.Float(compute='_compute_quote_count',
                                   string='Quote')

    @api.model
    def create(self, vals):
        res = super(Product, self).create(vals)
        if res:
            supplier = self.env.ref('cantrio_custom.res_partner_dummy_vendor')
            flag = self.seller_ids.create(
                {'name': supplier.id, 'product_tmpl_id': res.id})
        return res

    #@api.multi
    def name_get(self):
        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code,name)
            return (d['id'], name)
        result = []
        for product in self.sudo():
            mydict = {
                      'id': product.id,
                      'name': product.name,
                      }
            if self.env.user.has_group('cantrio_custom.group_sale_director'):
                mydict['default_code'] = product.default_code
            result.append(_name_get(mydict))
        return result


class ProductProduct(models.Model):
    _inherit = "product.product"

    #@api.multi
    def name_get(self):
        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code,name)
            return (d['id'], name)
        result = []
        for product in self.sudo():
            mydict = {
                      'id': product.id,
                      'name': product.name,
                      }
            if self.env.user.has_group('cantrio_custom.group_sale_director'):
                mydict['default_code'] = product.default_code
            result.append(_name_get(mydict))
        return result

